import os
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from google.cloud import storage

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
RAW_FOLDER = "raw"
PROCESSED_FOLDER = "processed"


# Configuración de logs
BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def filter_invalid_observations(df: pd.DataFrame) -> pd.DataFrame:
    """Mantiene solo observaciones válidas (obsValid == True)."""
    return df[df["obsValid"] == True].copy()

def drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina columnas irrelevantes para el análisis:
    - locName: campo libre no estandarizado
    - exoticCategory: mayormente nulo
    - locationPrivate: irrelevante para tendencias
    - obsReviewed: revisión manual, no aporta en este análisis
    """
    cols_to_drop = ["locName", "exoticCategory", "locationPrivate", "obsReviewed"]
    return df.drop(columns=[c for c in cols_to_drop if c in df.columns])

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados basados en subId + speciesCode."""
    return df.drop_duplicates(subset=["subId", "speciesCode"])

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte obsDt a datetime (agregando hora si falta)
    y extrae columnas auxiliares como enteros compatibles con BigQuery."""
    df = df.copy()

    # Asegura que todas las fechas tengan hora (agrega 00:00 si falta)
    df["obsDt"] = df["obsDt"].apply(lambda x: f"{x} 00:00" if isinstance(x, str) and len(x) == 10 else x)

    df["obsDt"] = pd.to_datetime(df["obsDt"], errors="coerce")

    # Extrae año, mes y día como enteros nulo-compatibles
    df["year"] = df["obsDt"].dt.year.astype("Int64")
    df["month"] = df["obsDt"].dt.month.astype("Int64")
    df["day"] = df["obsDt"].dt.day.astype("Int64")

    return df


def clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura que lat/lng sean numéricos y elimina nulos."""
    df = df.copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").round(6)
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce").round(6)

    # Crear columna tipo POINT para BigQuery GEOGRAPHY
    df["location"] = df.apply(lambda row: f"POINT({row['lng']} {row['lat']})", axis=1)
    return df

def handle_howmany(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maneja la columna howMany:
    - Elimina registros con howMany nulo.
    - Elimina registros con howMany == 0 (inconsistentes).
    """
    df = df.copy()
    df["howMany"] = pd.to_numeric(df["howMany"], errors="coerce")
    df = df[df["howMany"].notnull() & (df["howMany"] > 0)]
    df["howMany"] = df["howMany"].astype(int)
    return df

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las transformaciones en orden lógico."""
    df = filter_invalid_observations(df)
    df = drop_irrelevant_columns(df)
    df = remove_duplicates(df)
    df = normalize_dates(df)
    df = clean_coordinates(df)
    df = handle_howmany(df)
    return df

def get_latest_raw_from_gcs():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=f"{RAW_FOLDER}/"))

    if not blobs:
        raise FileNotFoundError("No se encontraron archivos en raw/ del bucket")

    latest_blob = max(blobs, key=lambda b: b.time_created)
    logging.info(f"Procesando archivo desde GCS: {latest_blob.name}")

    data = latest_blob.download_as_text(encoding="utf-8")
    df = pd.read_json(data)
    return df, latest_blob.name

def upload_processed_to_gcs(df, region_code="unknown"):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{PROCESSED_FOLDER}/ebird_{region_code}_processed_{timestamp}.csv"

    blob = bucket.blob(filename)
    blob.upload_from_string(df.to_csv(index=False, encoding="utf-8"),content_type="text/csv")

    gcs_uri = f"gs://{BUCKET_NAME}/{filename}"
    logging.info(f"Procesado subido a {gcs_uri}")
    return gcs_uri


if __name__ == "__main__":
    try:
        df_raw, raw_filename = get_latest_raw_from_gcs()
        df_clean = clean_dataset(df_raw)

        parts = Path(raw_filename).stem.split("_")
        region_code = parts[1] if len(parts) > 1 else "unknown"
        df_clean["region_code"] = region_code

        gcs_uri = upload_processed_to_gcs(df_clean, region_code=region_code)

        logging.info("Transformación completada y subida a GCS")
    except Exception:
        logging.exception("Fallo en la transformación de datos")

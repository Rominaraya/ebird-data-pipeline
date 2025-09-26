import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Directorios
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de logs
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
    """Convierte obsDt a datetime y agrega columnas auxiliares."""
    df = df.copy()
    df["obsDt"] = pd.to_datetime(df["obsDt"], errors="coerce")
    df["year"] = df["obsDt"].dt.year
    df["month"] = df["obsDt"].dt.month
    df["day"] = df["obsDt"].dt.day
    return df


def clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura que lat/lng sean numéricos y elimina nulos."""
    df = df.copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").round(6)
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce").round(6)
    return df.dropna(subset=["lat", "lng"])

def handle_howmany(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maneja la columna howMany:
    - Elimina registros con howMany nulo.
    - Elimina registros con howMany == 0 (inconsistentes).
    """
    df = df.copy()
    df = df.dropna(subset=["howMany"])
    df = df[df["howMany"] > 0]
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

def save_processed_data(df: pd.DataFrame, region_code="CL-RM"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = PROCESSED_DATA_DIR / f"ebird_{region_code}_processed_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding="utf-8")
    logging.info(f"Datos procesados guardados en {filename}")


if __name__ == "__main__":
    try:
        latest_file = max(RAW_DATA_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
        logging.info(f"Procesando archivo: {latest_file}")

        df_raw = pd.read_json(latest_file)

        df_clean = clean_dataset(df_raw)

        region_code = latest_file.stem.split("_")[1]
        save_processed_data(df_clean, region_code=region_code)

    except Exception:
        logging.exception("Fallo en la transformación de datos")

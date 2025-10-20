import os
import logging
from pathlib import Path
from google.cloud import storage, bigquery

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
PROCESSED_FOLDER = "processed"

BQ_DATASET = "ebird_data"
BQ_TABLE = "ebird_avistamientos"

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

def get_latest_processed_from_gcs():
    """Obtiene el último archivo procesado en GCS."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=f"{PROCESSED_FOLDER}/"))

    if not blobs:
        raise FileNotFoundError("No se encontraron archivos en processed/ del bucket")

    latest_blob = max(blobs, key=lambda b: b.time_created)
    gcs_uri = f"gs://{BUCKET_NAME}/{latest_blob.name}"
    logging.info(f"Último archivo procesado: {gcs_uri}")
    return gcs_uri

def load_to_bigquery(gcs_uri: str):
    """Carga un archivo CSV desde GCS a BigQuery."""
    client = bigquery.Client()
    table_id = f"{client.project}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition="WRITE_APPEND",  # o "WRITE_TRUNCATE" si quieres recrear la tabla
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="obsDt"
        ),
        schema=[
            bigquery.SchemaField("speciesCode", "STRING"),
            bigquery.SchemaField("comName", "STRING"),
            bigquery.SchemaField("sciName", "STRING"),
            bigquery.SchemaField("locId", "STRING"),
            bigquery.SchemaField("obsDt", "TIMESTAMP"),
            bigquery.SchemaField("howMany", "INTEGER"),
            bigquery.SchemaField("lat", "FLOAT"),
            bigquery.SchemaField("lng", "FLOAT"),
            bigquery.SchemaField("obsValid", "BOOLEAN"),
            bigquery.SchemaField("subId", "STRING"),
            bigquery.SchemaField("year", "INTEGER"),
            bigquery.SchemaField("month", "INTEGER"),
            bigquery.SchemaField("day", "INTEGER"),
            bigquery.SchemaField("location", "GEOGRAPHY"),
            bigquery.SchemaField("region_code", "STRING"),
        ]
    )
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    logging.info(f"Datos cargados en BigQuery: {table_id}")

if __name__ == "__main__":
    try:
        latest_uri = get_latest_processed_from_gcs()
        load_to_bigquery(latest_uri)
        logging.info("Carga a BigQuery completada")
    except Exception as e:
        logging.exception(f"Fallo en la carga de datos a BigQuery: {e}")
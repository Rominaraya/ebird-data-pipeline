import os
import requests
import json
import logging
from pathlib import Path
from datetime import datetime
from google.cloud import storage

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

API_URL = "https://api.ebird.org/v2/data/obs/{regionCode}/recent"
API_KEY = os.getenv("EBIRD_API_KEY")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
RAW_FOLDER = "raw"

if not API_KEY:
    raise RuntimeError("Falta EBIRD_API_KEY en el entorno.")
if not BUCKET_NAME:
    raise RuntimeError("Falta GCS_BUCKET_NAME en el entorno.")
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    logging.warning("GOOGLE_APPLICATION_CREDENTIALS no está definido.")


def fetch_recent_observations(region_code="CL", max_results=50, back_days=1, locale="es"):
    """
    Descarga observaciones recientes desde la API de eBird.

    :param region_code: Código de región (ej. 'CL' o 'CL-RM')
    :param max_results: Máximo de registros a devolver
    :param back_days: Días hacia atrás desde hoy
    :param locale: Idioma de nombres comunes (ej. 'es')
    :return: lista de observaciones (dicts)
    """
    url = API_URL.format(regionCode=region_code)
    headers = {"x-ebirdapitoken": API_KEY}
    params = {
        "maxResults": max_results,
        "back": back_days,
        "sppLocale": locale
    }

    logging.info(f"Solicitando datos de la región {region_code} con {max_results} resultados máximos")

    response = requests.get(url, headers=headers, params=params, timeout=60)

    if response.status_code == 200:
        logging.info("Datos recibidos correctamente desde la API")
        return response.json()
    else:
        logging.error(f"Error {response.status_code}: {response.text}")
        raise Exception(f"Error {response.status_code}: {response.text}")

def upload_raw_to_gcs(data, region_code: str):

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{RAW_FOLDER}/ebird_{region_code}_{timestamp}.json"

    blob = bucket.blob(filename)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )

    logging.info(f"Datos subidos a gs://{BUCKET_NAME}/{filename}")

if __name__ == "__main__":
    try:
        observations = fetch_recent_observations(
            region_code="US",
            max_results=10,
            back_days=1
        )
        upload_raw_to_gcs(observations, region_code="US")
    except Exception:
        logging.exception("Fallo en la ingesta de datos")



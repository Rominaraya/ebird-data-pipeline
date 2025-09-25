import os
import requests
import json
from pathlib import Path
from datetime import datetime

API_URL = "https://api.ebird.org/v2/data/obs/{regionCode}/recent"
API_KEY = os.getenv("EBIRD_API_KEY")


RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_recent_observations(region_code="CL-RM", max_results=50, back_days=7, locale="es"):
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

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")


def save_raw_data(data, region_code="CL-RM"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = RAW_DATA_DIR / f"ebird_{region_code}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Datos guardados en {filename}")


if __name__ == "__main__":
    observations = fetch_recent_observations(region_code="CL-RM", max_results=20)
    save_raw_data(observations, region_code="CL-RM")


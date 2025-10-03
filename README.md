# 🐦 eBird Data Pipeline
[![Pipeline eBird](https://github.com/Rominaraya/ebird-data-pipeline/actions/workflows/pipeline_ebird.yml/badge.svg)](https://github.com/Rominaraya/ebird-data-pipeline/actions/workflows/pipeline_ebird.yml)
![Python](https://img.shields.io/badge/python-3.13.7-blue.svg)

Pipeline automatizado para la recolección, transformación y almacenamiento de datos de observaciones de aves de la localidad seleccionada, utilizando la API de eBird, Google Cloud Storage y BigQuery.  
La ejecución está programada y gestionada mediante GitHub Actions.

## Uso de datos de eBird
Los datos utilizados en este proyecto provienen de la API pública de eBird.  
Fuente recomendada para citación:  
eBird. 2025. eBird Basic Dataset. Cornell Lab of Ornithology, Ithaca, New York.

## Intención del proyecto
El objetivo principal es crear un flujo de datos automatizado, reproducible y escalable que permita:

- Obtener registros actualizados por día de observaciones de aves de una localidad específica desde la API de eBird.
- Procesar y limpiar los datos para asegurar consistencia y trazabilidad.
- Almacenarlos en Google Cloud Storage y BigQuery para análisis posteriores.

---

## Funcionalidad

1. **Ingesta (`ingest.py`)**  
   - Consulta la API de eBird para obtener observaciones del día anterior de una localidad seleccionada.  
   - Genera archivos crudos y los sube a Google Cloud Storage en la carpeta `raw/`.

2. **Transformación (`transform.py`)**  
   - Descarga los archivos desde `raw/`.  
   - Convierte los datos a formato tabular (CSV).  
   - Añade campos de control como `timestamp` (hora de observación) y `execution_time` (hora de ejecución del pipeline).  
   - Estandariza columnas y elimina duplicados.  
   - Guarda los resultados en la carpeta `processed/` y en GCS.

3. **Carga (`load.py`)**  
   - Toma el último archivo procesado.  
   - Inserta los datos en una tabla de BigQuery (`ebird_data.observations`).  

4. **Orquestación (`run_pipeline.py`)**  
   - Ejecuta en orden los pasos de ingesta, transformación y carga.  
   - Incluye logging y control de errores para trazabilidad.

5. **Automatización (`.github/workflows/pipeline_ebird.yml`)**  
   - Ejecución programada todos los días a las 12:00 hora de Chile (15:00 UTC).  
   - Ejecución manual disponible mediante `workflow_dispatch`.  
   - Configuración de entorno y autenticación a GCP mediante secretos.

---

## Variables de entorno

El pipeline requiere las siguientes variables (configuradas como GitHub Secrets o en un archivo `.env` local):

- `EBIRD_API_KEY` → API key de eBird.  
- `GCS_BUCKET_NAME` → Nombre del bucket en Google Cloud Storage.  
- `GCP_CREDENTIALS` → Credenciales JSON de servicio para GCP.  

---
## Obtención de la API Key de eBird

Para ejecutar este pipeline es necesario contar con una API Key personal de eBird.  
El proceso para obtenerla es el siguiente:

1. Crear una cuenta gratuita en [eBird](https://ebird.org) si aún no la tienes.  
2. Iniciar sesión y dirigirse a la página de [solicitud de API Key](https://documenter.getpostman.com/view/664302/S1ENwy59).  
3. Generar la clave y copiarla.  
4. Configurarla como variable de entorno `EBIRD_API_KEY` en tu entorno local o en los Secrets de GitHub Actions.  

---

## Tecnologías utilizadas

- Python 3.13.7  
- eBird API  
- Google Cloud Storage  
- Google BigQuery  
- GitHub Actions (automatización)  
- Pandas (procesamiento de datos)

---

## Ejecución local

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pipeline
python src/run_pipeline.py

---
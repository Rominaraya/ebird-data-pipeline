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

- Obtener registros actualizados por día de observaciones de aves en una región específica.
- Limpiar, validar y enriquecer los datos para análisis  asegurar consistencia y trazabilidad.
- Almacenarlos en Google Cloud Storage y BigQuery para análisis posteriores.

---

## Funcionalidad

1. **Ingesta (`ingest.py`)**  
   - Consulta la API de eBird para obtener observaciones del día anterior.  
   - Guarda los datos en formato JSON en la carpeta raw/ del bucket de GCS.

2. **Transformación (`transform.py`)**  
   - Descarga el archivo más reciente desde raw/. 
   - Aplica limpieza y validación:  
     - Filtra observaciones válidas (obsValid = True)  
     - Elimina columnas irrelevantes (locName, exoticCategory, etc.)  
     - Elimina duplicados (subId + speciesCode)
     - Normaliza fechas (obsDt) y extrae year, month, day
     - Convierte coordenadas a GEOGRAPHY (POINT(lng lat))
     - Filtra registros con howMany nulo o igual a 0
   - Añade la columna region_code extraída del nombre del archivo.
   - Guarda el resultado como CSV en la carpeta processed/ del bucket.

3. **Carga (`load.py`)**  
   - Obtiene el último archivo procesado desde GCS. 
   - Carga los datos a BigQuery en la tabla ebird_data.ebird_avistamientos. 
   - Define el esquema manualmente, incluyendo tipos como TIMESTAMP, GEOGRAPHY, INTEGER, etc.
   - Usa WRITE_APPEND para conservar el histórico.

4. **Orquestación (`run_pipeline.py`)**  
   - Ejecuta los pasos de ingesta, transformación y carga en orden.  
   - Incluye logging y control de errores para trazabilidad.

5. **Automatización (`.github/workflows/pipeline_ebird.yml`)**  
   - Ejecución programada todos los días a las 12:00 hora de Chile (15:00 UTC).  
   - Ejecución manual disponible mediante `workflow_dispatch`.  
   - Configuración de entorno y autenticación a GCP mediante secretos.

---

## Variables de entorno

El pipeline requiere las siguientes variables (configuradas como GitHub Secrets o en un archivo `.env` local):

- `EBIRD_API_KEY` → Clave de acceso a la API de eBird
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

```
---
## Visualización de datos de avistamientos de aves en Chile
Esta sección muestra ejemplos de análisis  realizados sobre los datos cargados en BigQuery. Las visualizaciones fueron creadas en Looker Studio
a partir de consultas SQL ejecutadas directamente sobre la tabla ebird_data.ebird_avistamientos.

###  Consulta 1: Top 10 registros con mayor cantidad observada en Chile

```sql
SELECT
  comName AS nombre,
  howMany AS cantidad_registrada
FROM
  `ebirds-data-pipeline.ebird_data.ebird_avistamientos`
ORDER BY howMany DESC
LIMIT 10;
```
Esta consulta muestra los 10 registros individuales con mayor cantidad de aves observadas en todo el histórico disponible.

### Gráfico: Top 10 especies más observadas
<img width="1085" height="707" alt="imagen" src="https://github.com/user-attachments/assets/ed27256b-7d70-4b08-9d03-7b887315f58c" />
Este gráfico muestra las especies con mayor cantidad total de avistamientos en el histórico disponible.


###  Consulta 1: Distribución espacial de observaciones de aves en Chile

```sql
SELECT
  location,
  comName AS especie,
  howMany AS cantidad
FROM
  `ebirds-data-pipeline.ebird_data.ebird_avistamientos`;
```

### Mapa: Distribución espacial de observaciones de aves en Chile
<img width="773" height="775" alt="imagen" src="https://github.com/user-attachments/assets/62045842-9bd1-4c62-98bc-ad1a3ab03e66" />

Este gráfico muestra los puntos geográficos donde se han registrado observaciones válidas de aves en Chile continental.
Los datos fueron obtenidos desde la API de eBird y procesados en BigQuery.

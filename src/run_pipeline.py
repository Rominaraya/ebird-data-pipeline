import logging
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

BASE_DIR = Path(__file__).resolve().parent
def run_step(script):
    script_path = BASE_DIR / script
    logging.info(f"▶ Ejecutando {script_path}...")
    result = subprocess.run(["python", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error en {script}:\n{result.stderr}")
        raise RuntimeError(f"{script} falló")
    logging.info(f"{script} completado")

if __name__ == "__main__":
    run_step("ingest.py")
    run_step("transform.py")
    run_step("load.py")
    logging.info("Pipeline completo")

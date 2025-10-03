import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
def run_step(script):
    logging.info(f"▶ Ejecutando {script}...")
    result = subprocess.run(["python", script], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error en {script}:\n{result.stderr}")
        raise RuntimeError(f"{script} falló")
    logging.info(f"{script} completado")

if __name__ == "__main__":
    run_step("ingest.py")
    run_step("transform.py")
    run_step("load.py")
    logging.info("Pipeline completo")

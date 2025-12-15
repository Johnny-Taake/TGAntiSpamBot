from app import init_container, run_bot
from logger import setup_logging, get_logger

setup_logging()
log = get_logger(__name__)

if __name__ == "__main__":
    log.info("Starting...")
    init_container()
    run_bot()
    log.info("Stopped.")

import logging
import sys

from utils.bigquery_setup import create_table_if_not_exists
from utils.insert_midias_pagas import insert_midias_pagas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando paid-media-job")
    create_table_if_not_exists()
    insert_midias_pagas()
    logger.info("Job finalizado com sucesso")


if __name__ == "__main__":
    main()
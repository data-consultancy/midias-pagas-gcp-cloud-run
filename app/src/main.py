import logging
import sys

from utils.bigquery_setup import create_midias_pagas_if_not_exists, create_dim_ad_if_not_exists
from utils.insert_midias_pagas import insert_midias_pagas
from utils.insert_dim_ad import insert_dim_ad

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando paid-media-job")
    create_midias_pagas_if_not_exists()
    create_dim_ad_if_not_exists()
    insert_midias_pagas()
    insert_dim_ad()
    logger.info("Job finalizado com sucesso")


if __name__ == "__main__":
    main()
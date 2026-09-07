import logging
import sys

from utils.bigquery_setup import (
    create_midias_pagas_if_not_exists,
    create_dim_campanha_if_not_exists,
    create_dim_ad_if_not_exists,
    create_dim_trafego_ga4_if_not_exists,
    create_fato_sessoes_ga4_if_not_exists,
)
from utils.insert_midias_pagas import insert_midias_pagas
from utils.insert_dim_campanha import insert_dim_campanha
from utils.insert_dim_ad import insert_dim_ad
from utils.insert_dim_trafego_ga4 import insert_dim_trafego_ga4
from utils.insert_fato_sessoes_ga4 import insert_fato_sessoes_ga4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando paid-media-job")
    create_midias_pagas_if_not_exists()
    create_dim_campanha_if_not_exists()
    create_dim_ad_if_not_exists()
    create_dim_trafego_ga4_if_not_exists()
    create_fato_sessoes_ga4_if_not_exists()
    insert_midias_pagas()
    insert_dim_campanha()
    insert_dim_ad()
    insert_dim_trafego_ga4()
    insert_fato_sessoes_ga4()
    logger.info("Job finalizado com sucesso")


if __name__ == "__main__":
    main()
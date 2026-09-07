import logging
import os
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_GA4 = os.environ.get("DATASET_GA4", "ga4_metrics_us")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_DIM_TRAFEGO_GA4 = os.environ.get("TABLE_DIM_TRAFEGO_GA4", "dim_trafego_ga4")
TABLE_FATO_SESSOES_GA4 = os.environ.get("TABLE_FATO_SESSOES_GA4", "fato_sessoes_ga4")

_SQL_PATH = Path(__file__).parent / "sql" / "fato_sessoes_ga4.sql"


def insert_fato_sessoes_ga4():
    client = bigquery.Client(project=PROJECT_ID)

    query = (
        _SQL_PATH.read_text()
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_GA4}", DATASET_GA4)
        .replace("{DATASET_SILVER}", DATASET_SILVER)
        .replace("{TABLE_DIM_TRAFEGO_GA4}", TABLE_DIM_TRAFEGO_GA4)
        .replace("{TABLE_FATO_SESSOES_GA4}", TABLE_FATO_SESSOES_GA4)
    )

    logger.info("Executando MERGE D-3 na tabela %s...", TABLE_FATO_SESSOES_GA4)
    client.query(query).result()
    logger.info("MERGE concluído. Tabela: %s", TABLE_FATO_SESSOES_GA4)

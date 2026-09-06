import logging
import os
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_BRONZE = os.environ.get("DATASET_BRONZE")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_DIM_AD = os.environ.get("TABLE_DIM_AD", "dim_ad")
FULL_LOAD = os.environ.get("FULL_LOAD", "")
REPROCESS_DATE = os.environ.get("REPROCESS_DATE", "")

_SQL_PATH = Path(__file__).parent / "sql" / "dim_ad.sql"


def _is_full_load() -> bool:
    return FULL_LOAD.strip().upper() == "TRUE"


def _resolve_target_date() -> str:
    reprocess_date = REPROCESS_DATE.strip()
    if reprocess_date:
        try:
            date.fromisoformat(reprocess_date)
        except ValueError:
            raise ValueError(f"REPROCESS_DATE inválida: '{reprocess_date}'. Use o formato YYYY-MM-DD.")
        logger.info("Modo reprocessamento: data alvo = %s", reprocess_date)
        return reprocess_date
    return (date.today() - timedelta(days=1)).isoformat()


def insert_dim_ad():
    client = bigquery.Client(project=PROJECT_ID)

    raw = _SQL_PATH.read_text()

    if _is_full_load():
        raw = raw.replace("= '{D_MINUS_1}'", "IS NOT NULL")
        logger.info("Modo carga full: lendo todos os registros para %s...", TABLE_DIM_AD)
    else:
        target_date = _resolve_target_date()
        raw = raw.replace("{D_MINUS_1}", target_date)
        logger.info("Modo incremental: data alvo = %s | tabela = %s", target_date, TABLE_DIM_AD)

    query = (
        raw
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_BRONZE}", DATASET_BRONZE)
        .replace("{DATASET_SILVER}", DATASET_SILVER)
        .replace("{TABLE_DIM_AD}", TABLE_DIM_AD)
    )

    client.query(query).result()
    logger.info("MERGE concluído. Tabela: %s", TABLE_DIM_AD)

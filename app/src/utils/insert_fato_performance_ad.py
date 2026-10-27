import logging
import os
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_BRONZE = os.environ.get("DATASET_BRONZE")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_FATO_PERFORMANCE_AD = os.environ.get("TABLE_FATO_PERFORMANCE_AD", "fato_performance_ad")
FULL_LOAD = os.environ.get("FULL_LOAD", "")
REPROCESS_DATE = os.environ.get("REPROCESS_DATE", "")

# As plataformas recontabilizam métricas (principalmente conversões) nos dias seguintes,
# e a gold recalcula D-3 até D-1; a fato acompanha a mesma janela.
_JANELA_INCREMENTAL_DIAS = 3

_SQL_PATH = Path(__file__).parent / "sql" / "fato_performance_ad.sql"


def _is_full_load() -> bool:
    return FULL_LOAD.strip().upper() == "TRUE"


def _resolve_janela() -> tuple[str, str]:
    reprocess_date = REPROCESS_DATE.strip()
    if reprocess_date:
        try:
            date.fromisoformat(reprocess_date)
        except ValueError:
            raise ValueError(f"REPROCESS_DATE inválida: '{reprocess_date}'. Use o formato YYYY-MM-DD.")
        logger.info("Modo reprocessamento: data alvo = %s", reprocess_date)
        return reprocess_date, reprocess_date

    data_fim = date.today() - timedelta(days=1)
    data_inicio = data_fim - timedelta(days=_JANELA_INCREMENTAL_DIAS - 1)
    return data_inicio.isoformat(), data_fim.isoformat()


def insert_fato_performance_ad():
    client = bigquery.Client(project=PROJECT_ID)

    if _is_full_load():
        filtro_data = "TRUE"
        logger.info("Modo carga full: recarregando todo o histórico de %s...", TABLE_FATO_PERFORMANCE_AD)
    else:
        data_inicio, data_fim = _resolve_janela()
        filtro_data = f"dt_referencia BETWEEN '{data_inicio}' AND '{data_fim}'"
        logger.info("Modo incremental: janela %s a %s | tabela = %s", data_inicio, data_fim, TABLE_FATO_PERFORMANCE_AD)

    query = (
        _SQL_PATH.read_text(encoding="utf-8")
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_BRONZE}", DATASET_BRONZE)
        .replace("{DATASET_SILVER}", DATASET_SILVER)
        .replace("{TABLE_FATO_PERFORMANCE_AD}", TABLE_FATO_PERFORMANCE_AD)
        .replace("{FILTRO_DATA}", filtro_data)
    )

    client.query(query).result()
    logger.info("DELETE + INSERT concluído. Tabela: %s", TABLE_FATO_PERFORMANCE_AD)

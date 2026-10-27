import logging
import os
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
DATASET_GOLD = os.environ.get("DATASET_GOLD", "midiapaga_gold")
TABLE_DIM_CAMPANHA = os.environ.get("TABLE_DIM_CAMPANHA", "dim_campanha")
TABLE_DIM_PLATAFORMA = os.environ.get("TABLE_DIM_PLATAFORMA", "dim_plataforma")
TABLE_FATO_PERFORMANCE_AD = os.environ.get("TABLE_FATO_PERFORMANCE_AD", "fato_performance_ad")
TABLE_FATO_SESSOES_GA4 = os.environ.get("TABLE_FATO_SESSOES_GA4", "fato_sessoes_ga4")
TABLE_FATO_PERFORMANCE_MIDIA = os.environ.get("TABLE_FATO_PERFORMANCE_MIDIA", "fato_performance_midia")
DATA_INICIO_GOLD = os.environ.get("DATA_INICIO_GOLD", "2026-01-01")
FULL_LOAD = os.environ.get("FULL_LOAD", "")
REPROCESS_DATE = os.environ.get("REPROCESS_DATE", "")

# fato_sessoes_ga4 reprocessa os últimos 3 dias (dados do GA4 chegam atrasados),
# então a carga incremental recalcula a mesma janela: D-3 até D-1.
_JANELA_INCREMENTAL_DIAS = 3

_SQL_PATH = Path(__file__).parent / "sql" / "fato_performance_midia.sql"


def _is_full_load() -> bool:
    return FULL_LOAD.strip().upper() == "TRUE"


def _resolve_janela() -> tuple[str, str]:
    data_minima = date.fromisoformat(DATA_INICIO_GOLD)

    if _is_full_load():
        return data_minima.isoformat(), date.today().isoformat()

    reprocess_date = REPROCESS_DATE.strip()
    if reprocess_date:
        try:
            date.fromisoformat(reprocess_date)
        except ValueError:
            raise ValueError(f"REPROCESS_DATE inválida: '{reprocess_date}'. Use o formato YYYY-MM-DD.")
        logger.info("Modo reprocessamento: data alvo = %s", reprocess_date)
        return reprocess_date, reprocess_date

    data_fim = date.today() - timedelta(days=1)
    data_inicio = max(data_fim - timedelta(days=_JANELA_INCREMENTAL_DIAS - 1), data_minima)
    return data_inicio.isoformat(), data_fim.isoformat()


def insert_fato_performance_midia():
    client = bigquery.Client(project=PROJECT_ID)

    data_inicio, data_fim = _resolve_janela()
    if _is_full_load():
        logger.info("Modo carga full: recalculando %s de %s a %s...", TABLE_FATO_PERFORMANCE_MIDIA, data_inicio, data_fim)
    else:
        logger.info("Modo incremental: janela %s a %s | tabela = %s", data_inicio, data_fim, TABLE_FATO_PERFORMANCE_MIDIA)

    query = (
        _SQL_PATH.read_text(encoding="utf-8")
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_SILVER}", DATASET_SILVER)
        .replace("{DATASET_GOLD}", DATASET_GOLD)
        .replace("{TABLE_DIM_CAMPANHA}", TABLE_DIM_CAMPANHA)
        .replace("{TABLE_DIM_PLATAFORMA}", TABLE_DIM_PLATAFORMA)
        .replace("{TABLE_FATO_PERFORMANCE_AD}", TABLE_FATO_PERFORMANCE_AD)
        .replace("{TABLE_FATO_SESSOES_GA4}", TABLE_FATO_SESSOES_GA4)
        .replace("{TABLE_FATO_PERFORMANCE_MIDIA}", TABLE_FATO_PERFORMANCE_MIDIA)
        .replace("{DATA_INICIO}", data_inicio)
        .replace("{DATA_FIM}", data_fim)
    )

    client.query(query).result()
    logger.info("DELETE + INSERT concluído. Janela: %s a %s | Tabela: %s", data_inicio, data_fim, TABLE_FATO_PERFORMANCE_MIDIA)

import logging
import os
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_BRONZE = os.environ.get("DATASET_BRONZE", "midiapaga_bronze")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_SILVER = os.environ.get("TABLE_SILVER")

_SQL_PATH = Path(__file__).parent / "sql" / "midias_pagas.sql"


def _build_insert_query(d_minus_1: str) -> str:
    source_sql = (
        _SQL_PATH.read_text()
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_BRONZE}", DATASET_BRONZE)
        .rstrip()
        .rstrip(";")
    )

    # Separa o bloco de CTEs do SELECT final para montar o INSERT
    cte_block = source_sql.rsplit("\nSELECT * FROM", 1)[0]
    target_table = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER}"

    return f"""\
INSERT INTO `{target_table}` (
    data,
    plataforma,
    campanha,
    conjunto_anuncio,
    anuncio,
    impressions,
    clicks,
    custo,
    conversoes,
    data_atualizacao
)
{cte_block}

SELECT
    data_registro        AS data,
    plataforma,
    campanha_nome        AS campanha,
    CAST(NULL AS STRING) AS conjunto_anuncio,
    anuncio_nome         AS anuncio,
    impressoes           AS impressions,
    cliques              AS clicks,
    investimento         AS custo,
    SAFE_CAST(conversoes AS INT64) AS conversoes,
    CURRENT_TIMESTAMP()  AS data_atualizacao
FROM (
    SELECT * FROM google_ads
    UNION ALL
    SELECT * FROM linkedin_ads
    UNION ALL
    SELECT * FROM meta_ads
    UNION ALL
    SELECT * FROM microsoft_ads
)
WHERE data_registro = '{d_minus_1}'
"""


def insert_midias_pagas():
    client = bigquery.Client(project=PROJECT_ID)
    d_minus_1 = (date.today() - timedelta(days=1)).isoformat()
    target_table = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER}"

    delete_query = f"DELETE FROM `{target_table}` WHERE data = '{d_minus_1}'"
    logger.info("Deletando registros D-1 (%s) da tabela %s...", d_minus_1, TABLE_SILVER)
    client.query(delete_query).result()

    insert_query = _build_insert_query(d_minus_1)
    logger.info("Inserindo dados D-1 (%s) na tabela %s...", d_minus_1, TABLE_SILVER)
    client.query(insert_query).result()
    logger.info("Insert concluído. Data: %s | Tabela: %s", d_minus_1, TABLE_SILVER)

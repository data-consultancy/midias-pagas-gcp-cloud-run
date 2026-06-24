import logging
import os
from datetime import date, timedelta
from pathlib import Path

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_BRONZE = os.environ.get("DATASET_BRONZE")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_SILVER = os.environ.get("TABLE_SILVER")

_SQL_PATH = Path(__file__).parent / "sql" / "midias_pagas.sql"


def _build_select_query(d_minus_1: str) -> str:
    cte_block = (
        _SQL_PATH.read_text()
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_BRONZE}", DATASET_BRONZE)
        .replace("{D_MINUS_1}", d_minus_1)
        .rstrip()
        .rstrip(";")
        .rsplit("\n\nSELECT", 1)[0]
    )

    return f"""\
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
"""


def insert_midias_pagas():
    client = bigquery.Client(project=PROJECT_ID)
    d_minus_1 = (date.today() - timedelta(days=1)).isoformat()
    partition_id = d_minus_1.replace("-", "")
    target_table = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER}"

    job_config = bigquery.QueryJobConfig(
        destination=f"{target_table}${partition_id}",
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
    )

    query = _build_select_query(d_minus_1)
    logger.info("Sobrescrevendo partição D-1 (%s) na tabela %s...", d_minus_1, TABLE_SILVER)
    client.query(query, job_config=job_config).result()
    logger.info("Insert concluído. Data: %s | Tabela: %s", d_minus_1, TABLE_SILVER)

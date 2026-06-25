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
FULL_LOAD = os.environ.get("FULL_LOAD", "")

_SQL_PATH = Path(__file__).parent / "sql" / "midias_pagas.sql"


def _build_select_query(d_minus_1: str | None, full_load: bool = False) -> str:
    raw = _SQL_PATH.read_text()
    if full_load:
        raw = raw.replace("= '{D_MINUS_1}'", "IS NOT NULL")
    cte_block = (
        raw
        .replace("{PROJECT_ID}", PROJECT_ID)
        .replace("{DATASET_BRONZE}", DATASET_BRONZE)
        .replace("{D_MINUS_1}", d_minus_1 or "")
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


def _is_full_load() -> bool:
    return FULL_LOAD.strip().upper() == "TRUE"


def _resolve_target_date() -> str:
    reprocess_date = os.environ.get("REPROCESS_DATE", "").strip()
    if reprocess_date:
        try:
            date.fromisoformat(reprocess_date)
        except ValueError:
            raise ValueError(f"REPROCESS_DATE inválida: '{reprocess_date}'. Use o formato YYYY-MM-DD.")
        logger.info("Modo reprocessamento: data alvo = %s", reprocess_date)
        return reprocess_date
    return (date.today() - timedelta(days=1)).isoformat()


def insert_midias_pagas():
    client = bigquery.Client(project=PROJECT_ID)
    target_table = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER}"

    if _is_full_load():
        job_config = bigquery.QueryJobConfig(
            destination=target_table,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
        )
        query = _build_select_query(None, full_load=True)
        logger.info("Modo carga full: sobrescrevendo tabela inteira %s...", TABLE_SILVER)
        client.query(query, job_config=job_config).result()
        logger.info("Carga full concluída. Tabela: %s", TABLE_SILVER)
    else:
        target_date = _resolve_target_date()
        partition_id = target_date.replace("-", "")
        job_config = bigquery.QueryJobConfig(
            destination=f"{target_table}${partition_id}",
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
        )
        query = _build_select_query(target_date)
        logger.info("Sobrescrevendo partição %s na tabela %s...", target_date, TABLE_SILVER)
        client.query(query, job_config=job_config).result()
        logger.info("Insert concluído. Data: %s | Tabela: %s", target_date, TABLE_SILVER)

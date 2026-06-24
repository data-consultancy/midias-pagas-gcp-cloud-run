import logging
import os
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_SILVER = os.environ.get("TABLE_SILVER")

SCHEMA = [
    bigquery.SchemaField("data", "DATE", mode="NULLABLE"),
    bigquery.SchemaField("plataforma", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("campanha", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("conjunto_anuncio", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("anuncio", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("impressions", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("clicks", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("custo", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("conversoes", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("data_atualizacao", "TIMESTAMP", mode="NULLABLE"),
]


def create_table_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_SILVER}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)
    logger.info("Dataset %s pronto.", DATASET_SILVER)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER}"
    table = bigquery.Table(table_ref, schema=SCHEMA)
    table.time_partitioning = bigquery.TimePartitioning(field="data")
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_SILVER)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_SILVER)

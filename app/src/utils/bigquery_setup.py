import logging
import os
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_SILVER_MIDIAS_PAGAS = os.environ.get("TABLE_SILVER_MIDIAS_PAGAS", "midias_pagas")
TABLE_DIM_AD = os.environ.get("TABLE_DIM_AD", "dim_ad")

SCHEMA_MIDIAS_PAGAS = [
    bigquery.SchemaField("data", "DATE", mode="NULLABLE"),
    bigquery.SchemaField("plataforma", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("campanha", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("anuncio", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("impressions", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("clicks", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("custo", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("conversoes", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("data_atualizacao", "TIMESTAMP", mode="NULLABLE"),
]

SCHEMA_DIM_AD = [
    bigquery.SchemaField("sk_ad", "STRING", mode="NULLABLE", description="Chave substituta única do anúncio (MD5)"),
    bigquery.SchemaField("sk_campanha", "STRING", mode="NULLABLE", description="Chave estrangeira apontando para a campanha"),
    bigquery.SchemaField("id_ad_original", "STRING", mode="NULLABLE", description="ID real do anúncio extraído da API"),
    bigquery.SchemaField("nm_ad", "STRING", mode="NULLABLE", description="Nome ou título descritivo do anúncio"),
    bigquery.SchemaField("ds_status_ad", "STRING", mode="NULLABLE", description="Status atual do anúncio"),
    bigquery.SchemaField("data_carga", "DATE", mode="NULLABLE", description="Data em que o registro foi inserido pela primeira vez"),
]


def create_midias_pagas_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_SILVER}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)
    logger.info("Dataset %s pronto.", DATASET_SILVER)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_SILVER_MIDIAS_PAGAS}"
    table = bigquery.Table(table_ref, schema=SCHEMA_MIDIAS_PAGAS)
    table.time_partitioning = bigquery.TimePartitioning(field="data")
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_SILVER_MIDIAS_PAGAS)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_SILVER_MIDIAS_PAGAS)


def create_dim_ad_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_AD}"
    table = bigquery.Table(table_ref, schema=SCHEMA_DIM_AD)
    table.clustering_fields = ["sk_ad", "sk_campanha"]
    table.description = "Dimensão de anúncios/criativos vinculados às campanhas."
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_DIM_AD)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_DIM_AD)

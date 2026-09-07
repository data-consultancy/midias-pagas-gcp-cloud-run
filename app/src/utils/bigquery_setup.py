import logging
import os
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_SILVER = os.environ.get("DATASET_SILVER")
TABLE_SILVER_MIDIAS_PAGAS = os.environ.get("TABLE_SILVER_MIDIAS_PAGAS", "midias_pagas")
TABLE_DIM_AD = os.environ.get("TABLE_DIM_AD", "dim_ad")
TABLE_DIM_CAMPANHA = os.environ.get("TABLE_DIM_CAMPANHA", "dim_campanha")
TABLE_DIM_TRAFEGO_GA4 = os.environ.get("TABLE_DIM_TRAFEGO_GA4", "dim_trafego_ga4")
TABLE_FATO_SESSOES_GA4 = os.environ.get("TABLE_FATO_SESSOES_GA4", "fato_sessoes_ga4")

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


SCHEMA_DIM_CAMPANHA = [
    bigquery.SchemaField("sk_campanha", "STRING", mode="NULLABLE", description="Chave substituta única gerada via MD5"),
    bigquery.SchemaField("sk_plataforma", "INT64", mode="NULLABLE", description="ID fixo da plataforma (FK)"),
    bigquery.SchemaField("id_campanha_original", "STRING", mode="NULLABLE", description="ID real da campanha extraído da API"),
    bigquery.SchemaField("nm_campanha", "STRING", mode="NULLABLE", description="Nome da campanha"),
    bigquery.SchemaField("ds_status_campanha", "STRING", mode="NULLABLE", description="Status atual da campanha"),
    bigquery.SchemaField("ds_objetivo_campanha", "STRING", mode="NULLABLE", description="Objetivo de marketing"),
    bigquery.SchemaField("dt_inicio_campanha", "DATE", mode="NULLABLE", description="Data de início da campanha"),
    bigquery.SchemaField("canal", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("tipo", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("objetivo", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("dif", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("funil", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("campanha_tratada", "STRING", mode="NULLABLE"),
]


SCHEMA_DIM_TRAFEGO_GA4 = [
    bigquery.SchemaField("traffic_sk", "INT64", mode="NULLABLE"),
    bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("medium", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("campaign", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("traffic_group", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("origem_ga4", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("source_medium", "STRING", mode="NULLABLE"),
]

SCHEMA_FATO_SESSOES_GA4 = [
    bigquery.SchemaField("data", "DATE", mode="NULLABLE"),
    bigquery.SchemaField("campanha", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("source_medium", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("sessoes_ga4", "INT64", mode="NULLABLE"),
]


def create_dim_trafego_ga4_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_TRAFEGO_GA4}"
    table = bigquery.Table(table_ref, schema=SCHEMA_DIM_TRAFEGO_GA4)
    table.clustering_fields = ["traffic_sk", "traffic_group"]
    table.description = "Materialização física da view vw_dTraffic para redução drástica de custos em scans. Atualizada via pipeline ELT."
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_DIM_TRAFEGO_GA4)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_DIM_TRAFEGO_GA4)


def create_fato_sessoes_ga4_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_FATO_SESSOES_GA4}"
    table = bigquery.Table(table_ref, schema=SCHEMA_FATO_SESSOES_GA4)
    table.time_partitioning = bigquery.TimePartitioning(field="data")
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_FATO_SESSOES_GA4)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_FATO_SESSOES_GA4)


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


def create_dim_campanha_if_not_exists():
    client = bigquery.Client(project=PROJECT_ID)

    table_ref = f"{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_CAMPANHA}"
    table = bigquery.Table(table_ref, schema=SCHEMA_DIM_CAMPANHA)
    table.clustering_fields = ["sk_campanha", "sk_plataforma"]
    table.description = "Dimensão de campanhas consolidadas das plataformas."
    try:
        client.create_table(table)
        logger.info("Tabela %s criada com sucesso.", TABLE_DIM_CAMPANHA)
    except Conflict:
        logger.info("Tabela %s já existe, nenhuma ação necessária.", TABLE_DIM_CAMPANHA)


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

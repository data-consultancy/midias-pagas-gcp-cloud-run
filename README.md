# paid-media-job

Job de ETL que consolida dados de mídia paga de múltiplas plataformas (Google Ads, LinkedIn Ads, Meta Ads e Microsoft Ads) da camada Bronze para a camada Silver no BigQuery.

## Visão geral

```
Bronze (raw por plataforma)
    ├── googleads_adperformance
    ├── linkedinads_ad_analytics_daily + linkedinads_creatives
    ├── metaads_reports
    └── microsoftads_ad
              │
              ▼
Silver (tabela unificada, particionada por data)
    └── <TABLE_SILVER>
```

A tabela Silver é particionada pelo campo `data` e possui o seguinte schema:

| Campo             | Tipo      | Descrição                        |
|-------------------|-----------|----------------------------------|
| data              | DATE      | Data do registro                 |
| plataforma        | STRING    | Nome da plataforma de anúncio    |
| campanha          | STRING    | Nome da campanha                 |
| conjunto_anuncio  | STRING    | Nome do conjunto de anúncio      |
| anuncio           | STRING    | Nome do anúncio                  |
| impressions       | INT64     | Número de impressões             |
| clicks            | INT64     | Número de cliques                |
| custo             | FLOAT64   | Investimento                     |
| conversoes        | INT64     | Número de conversões             |
| data_atualizacao  | TIMESTAMP | Timestamp da última atualização  |

## Estrutura do projeto

```
.
├── Dockerfile
├── cloudbuild.yaml
└── app/
    ├── requirements.txt
    └── src/
        ├── main.py
        └── utils/
            ├── bigquery_setup.py       # Cria dataset e tabela Silver se não existirem
            ├── insert_midias_pagas.py  # Lógica de carga incremental e full
            └── sql/
                └── midias_pagas.sql    # Query de transformação Bronze → Silver
```

## Variáveis de ambiente

| Variável         | Obrigatória | Descrição                                                                 |
|------------------|-------------|---------------------------------------------------------------------------|
| `PROJECT_ID`     | Sim         | ID do projeto GCP                                                         |
| `DATASET_BRONZE` | Sim         | Nome do dataset Bronze no BigQuery                                        |
| `DATASET_SILVER` | Sim         | Nome do dataset Silver no BigQuery                                        |
| `TABLE_SILVER`   | Sim         | Nome da tabela Silver de destino                                          |
| `REPROCESS_DATE` | Não         | Data específica para reprocessamento no formato `YYYY-MM-DD`              |
| `FULL_LOAD`      | Não         | Defina como `TRUE` para realizar carga completa (sobrescreve a tabela inteira) |

## Modos de execução

### Incremental (padrão)

Carrega apenas a partição do dia anterior (D-1). É o comportamento padrão quando nenhuma variável adicional é definida.

```bash
python app/src/main.py
```

### Reprocessamento de data específica

Sobrescreve a partição de uma data específica.

```bash
REPROCESS_DATE=2025-01-15 python app/src/main.py
```

### Carga full

Remove todos os dados da tabela Silver e recarrega o histórico completo das tabelas Bronze, sem filtro de data.

```bash
FULL_LOAD=TRUE python app/src/main.py
```

> **Atenção:** A carga full executa um `WRITE_TRUNCATE` na tabela inteira. Use com cautela em produção.

## Deploy

### Build e push da imagem (Cloud Build)

```bash
gcloud builds submit --config cloudbuild.yaml
```

A imagem é publicada em:
```
gcr.io/jota-dados-integracao-ga4/paid-media-job:latest
```

### Executar localmente com Docker

```bash
docker build -t paid-media-job .

docker run \
  -e PROJECT_ID=meu-projeto \
  -e DATASET_BRONZE=bronze \
  -e DATASET_SILVER=silver \
  -e TABLE_SILVER=midias_pagas \
  -v ~/.config/gcloud:/root/.config/gcloud \
  paid-media-job
```

## Execução no Cloud Run Jobs

O job é projetado para rodar como um **Cloud Run Job**. As variáveis de ambiente são configuradas diretamente no job. Para acionar modos específicos, sobrescreva as variáveis na execução:

```bash
# Carga incremental (execução normal via trigger agendado)
gcloud run jobs execute paid-media-job

# Reprocessamento de data específica
gcloud run jobs execute paid-media-job \
  --update-env-vars REPROCESS_DATE=2025-01-15

# Carga full
gcloud run jobs execute paid-media-job \
  --update-env-vars FULL_LOAD=TRUE
```

## Dependências

- `google-cloud-bigquery`
- `google-cloud-secret-manager`
- `requests`
- Python 3.11+

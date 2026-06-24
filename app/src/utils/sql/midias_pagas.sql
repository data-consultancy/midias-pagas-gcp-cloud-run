WITH google_ads AS (
SELECT
SAFE_CAST(Report__Date AS DATE) AS data_registro,
'Google Ads' AS plataforma,
SAFE_CAST(Account__Account_Id AS STRING) AS conta_id,
Account__Account_name AS conta_nome,
SAFE_CAST(Campaign__Campaign_Id AS STRING) AS campanha_id,
Campaign__Campaign_name AS campanha_nome,
Campaign__Campaign_status AS campanha_status, -- Adicionado
SAFE_CAST(Ad__Ad_Id AS STRING) AS anuncio_id,
Ad__Ad_name AS anuncio_nome,
Ad__Ad_status AS anuncio_status, -- Adicionado
SAFE_CAST(Cost__Amount_spend AS FLOAT64) AS investimento,
SAFE_CAST(Performance__Impressions AS INT64) AS impressoes,
SAFE_CAST(Performance__Clicks AS INT64) AS cliques,
SAFE_CAST(Conversions__Conversions AS FLOAT64) AS conversoes
FROM `{PROJECT_ID}.{DATASET_BRONZE}.googleads_adperformance`
),

linkedin_ads AS (
SELECT
SAFE_CAST(daily.Report__Date AS DATE) AS data_registro,
'LinkedIn Ads' AS plataforma,
SAFE_CAST(daily.Account__Account_Id AS STRING) AS conta_id,
daily.Account__Account_name AS conta_nome,
SAFE_CAST(daily.Campaign__Campaign_Id AS STRING) AS campanha_id,
daily.Campaign__Campaign_name AS campanha_nome,
daily.Campaign__Campaign_status AS campanha_status, -- Adicionado
SAFE_CAST(cr.id AS STRING) AS anuncio_id,
cr.name AS anuncio_nome,
cr.intended_status AS anuncio_status, -- Adicionado (Status do Criativo)
SAFE_CAST(daily.Cost__Amount_spend AS FLOAT64) AS investimento,
SAFE_CAST(daily.Performance__Impressions AS INT64) AS impressoes,
SAFE_CAST(daily.Performance__Clicks AS INT64) AS cliques,
SAFE_CAST(daily.Performance__Conversions AS FLOAT64) AS conversoes
FROM `{PROJECT_ID}.{DATASET_BRONZE}.linkedinads_ad_analytics_daily` daily
LEFT JOIN `{PROJECT_ID}.{DATASET_BRONZE}.linkedinads_creatives` cr
ON SAFE_CAST(daily.Campaign__Campaign_Id AS INT64) = cr.campaign_id
),

meta_ads AS (
SELECT
SAFE_CAST(Report__Date AS DATE) AS data_registro,
'Meta Ads' AS plataforma,
SAFE_CAST(NULL AS STRING) AS conta_id,
Account__Account_name AS conta_nome,
SAFE_CAST(Campaign__Campaign_Id AS STRING) AS campanha_id,
Campaign__Campaign_name AS campanha_nome,
-- Como a tabela 'metaads_reports' não veio com coluna de status, buscamos o status ideal na tabela de configurações da campanha se necessário.
-- Para fins de consolidação direta no report, deixamos como string estática ou NULL caso não mapeado no grão diário.
SAFE_CAST(NULL AS STRING) AS campanha_status,
SAFE_CAST(NULL AS STRING) AS anuncio_id,
SAFE_CAST(NULL AS STRING) AS anuncio_nome,
SAFE_CAST(NULL AS STRING) AS anuncio_status,
SAFE_CAST(Cost__Amount_spend AS FLOAT64) AS investimento,
SAFE_CAST(Performance__Impressions AS INT64) AS impressoes,
SAFE_CAST(Performance__Clicks AS INT64) AS cliques,
SAFE_CAST(NULL AS FLOAT64) AS conversoes
FROM `{PROJECT_ID}.{DATASET_BRONZE}.metaads_reports`
),

microsoft_ads AS (
SELECT
SAFE_CAST(TimePeriod AS DATE) AS data_registro,
'Microsoft Ads' AS plataforma,
SAFE_CAST(AccountId AS STRING) AS conta_id,
AccountName AS conta_nome,
SAFE_CAST(NULL AS STRING) AS campanha_id,
SAFE_CAST(NULL AS STRING) AS campanha_nome,
SAFE_CAST(NULL AS STRING) AS campanha_status,
SAFE_CAST(AdId AS STRING) AS anuncio_id,
AdTitle AS anuncio_nome,
AdStatus AS anuncio_status, -- Adicionado
SAFE_CAST(Spend AS FLOAT64) AS investimento,
SAFE_CAST(Impressions AS INT64) AS impressoes,
SAFE_CAST(Clicks AS INT64) AS cliques,
SAFE_CAST(Conversions AS FLOAT64) AS conversoes
FROM `{PROJECT_ID}.{DATASET_BRONZE}.microsoftads_ad`
)

SELECT * FROM google_ads
UNION ALL
SELECT * FROM linkedin_ads
UNION ALL
SELECT * FROM meta_ads
UNION ALL
SELECT * FROM microsoft_ads;
BEGIN TRANSACTION;

-- Remove o período que será recarregado (no full load, a tabela inteira) para evitar duplicidade.
-- TRUNCATE não é permitido dentro de transação, por isso DELETE.
DELETE FROM `{PROJECT_ID}.{DATASET_SILVER}.{TABLE_FATO_PERFORMANCE_AD}`
WHERE {FILTRO_DATA};

INSERT INTO `{PROJECT_ID}.{DATASET_SILVER}.{TABLE_FATO_PERFORMANCE_AD}` (
    dt_referencia, sk_plataforma, sk_campanha, sk_ad, vl_custo, nr_impressoes, nr_cliques, nr_conversoes
)
WITH staging_fato AS (
    -- 1. Google Ads
    SELECT
        SAFE_CAST(Report__Date AS DATE) AS dt_referencia,
        2 AS sk_plataforma,
        CAST(Campaign__Campaign_Id AS STRING) AS id_campanha_original,
        CAST(Ad__Ad_Id AS STRING) AS id_ad_original,
        SAFE_CAST(Cost__Amount_spend AS NUMERIC) AS vl_custo,
        SAFE_CAST(Performance__Impressions AS INT64) AS nr_impressoes,
        SAFE_CAST(Performance__Clicks AS INT64) AS nr_cliques,
        SAFE_CAST(Conversions__Conversions AS NUMERIC) AS nr_conversoes
    FROM `{PROJECT_ID}.{DATASET_BRONZE}.googleads_adperformance`

    UNION ALL

    -- 2. Meta Ads
    SELECT
        SAFE_CAST(Report__Date AS DATE) AS dt_referencia,
        1 AS sk_plataforma,
        CAST(Campaign__Campaign_Id AS STRING) AS id_campanha_original,
        CAST(Ad__Ad_Id AS STRING) AS id_ad_original,
        SAFE_CAST(Cost__Amount_spend AS NUMERIC) AS vl_custo,
        SAFE_CAST(Performance__Impressions AS INT64) AS nr_impressoes,
        SAFE_CAST(Performance__Clicks AS INT64) AS nr_cliques,
        SAFE_CAST(Conversions_Leads__Total AS NUMERIC) AS nr_conversoes
    FROM `{PROJECT_ID}.{DATASET_BRONZE}.metaads_reports`

    UNION ALL

    -- 3. LinkedIn Ads
    SELECT
        SAFE_CAST(Report__Date AS DATE) AS dt_referencia,
        4 AS sk_plataforma,
        REGEXP_EXTRACT(CAST(Campaign__Campaign_Id AS STRING), r'(\d+)') AS id_campanha_original,
        CAST(NULL AS STRING) AS id_ad_original,
        SAFE_CAST(Cost__Amount_spend AS NUMERIC) AS vl_custo,
        SAFE_CAST(Performance__Impressions AS INT64) AS nr_impressoes,
        SAFE_CAST(Performance__Clicks AS INT64) AS nr_cliques,
        SAFE_CAST(Performance__Conversions AS NUMERIC) AS nr_conversoes
    FROM `{PROJECT_ID}.{DATASET_BRONZE}.linkedinads_ad_analytics_daily`

    UNION ALL

    -- 4. Microsoft Ads
    SELECT
        SAFE_CAST(TimePeriod AS DATE) AS dt_referencia,
        3 AS sk_plataforma,
        CAST(CampaignId AS STRING) AS id_campanha_original,
        CAST(AdId AS STRING) AS id_ad_original,
        SAFE_CAST(Spend AS NUMERIC) AS vl_custo,
        SAFE_CAST(Impressions AS INT64) AS nr_impressoes,
        SAFE_CAST(Clicks AS INT64) AS nr_cliques,
        SAFE_CAST(Conversions AS NUMERIC) AS nr_conversoes
    FROM `{PROJECT_ID}.{DATASET_BRONZE}.microsoftads_ad`
)
SELECT
    dt_referencia,
    sk_plataforma,
    -- Mesma regra de chave da dim_campanha / dim_ad, garantindo o JOIN
    IF(id_campanha_original IS NULL, NULL, TO_HEX(MD5(CONCAT(CAST(sk_plataforma AS STRING), '||', id_campanha_original)))) AS sk_campanha,
    IF(id_ad_original IS NULL, NULL, TO_HEX(MD5(CONCAT(CAST(sk_plataforma AS STRING), '||', id_ad_original)))) AS sk_ad,
    vl_custo,
    nr_impressoes,
    nr_cliques,
    nr_conversoes
FROM staging_fato
WHERE dt_referencia IS NOT NULL
AND {FILTRO_DATA};

COMMIT TRANSACTION;

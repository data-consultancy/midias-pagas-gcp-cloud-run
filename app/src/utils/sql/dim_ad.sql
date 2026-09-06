MERGE INTO `{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_AD}` T
USING (
    WITH staging_ads AS (
        SELECT DISTINCT
            2 AS sk_plataforma,
            CAST(Campaign__Campaign_Id AS STRING) AS id_campanha_original,
            CAST(Ad__Ad_Id AS STRING) AS id_ad_original,
            Ad__Ad_name AS nm_ad,
            Ad__Ad_status AS ds_status_ad
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.googleads_adperformance`
        WHERE Ad__Ad_Id IS NOT NULL
        AND SAFE_CAST(Report__Date AS DATE) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            1 AS sk_plataforma,
            CAST(Campaign__Campaign_Id AS STRING) AS id_campanha_original,
            CAST(Ad__Ad_Id AS STRING) AS id_ad_original,
            Ad__Ad_name AS nm_ad,
            CAST(NULL AS STRING) AS ds_status_ad
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.metaads_reports`
        WHERE Ad__Ad_Id IS NOT NULL
        AND SAFE_CAST(Report__Date AS DATE) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            4 AS sk_plataforma,
            REGEXP_EXTRACT(CAST(campaign_id AS STRING), r'(\d+)') AS id_campanha_original,
            REGEXP_EXTRACT(CAST(id AS STRING), r'(\d+)') AS id_ad_original,
            name AS nm_ad,
            intended_status AS ds_status_ad
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.linkedinads_creatives`
        WHERE id IS NOT NULL
        AND DATE(Row_Updated_At) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            3 AS sk_plataforma,
            CAST(CampaignId AS STRING) AS id_campanha_original,
            CAST(AdId AS STRING) AS id_ad_original,
            AdTitle AS nm_ad,
            AdStatus AS ds_status_ad
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.microsoftads_ad`
        WHERE AdId IS NOT NULL
        AND SAFE_CAST(TimePeriod AS DATE) = '{D_MINUS_1}'
    )
    SELECT
        TO_HEX(MD5(CONCAT(CAST(sk_plataforma AS STRING), '||', id_ad_original))) AS sk_ad,
        IF(
            id_campanha_original IS NULL,
            NULL,
            TO_HEX(MD5(CONCAT(CAST(sk_plataforma AS STRING), '||', id_campanha_original)))
        ) AS sk_campanha,
        id_ad_original,
        nm_ad,
        ds_status_ad
    FROM staging_ads
) S
ON T.sk_ad = S.sk_ad
WHEN MATCHED THEN
    UPDATE SET
        T.nm_ad = S.nm_ad,
        T.ds_status_ad = S.ds_status_ad
WHEN NOT MATCHED THEN
    INSERT (sk_ad, sk_campanha, id_ad_original, nm_ad, ds_status_ad, data_carga)
    VALUES (S.sk_ad, S.sk_campanha, S.id_ad_original, S.nm_ad, S.ds_status_ad, CURRENT_DATE());

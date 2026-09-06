MERGE INTO `{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_CAMPANHA}` T
USING (
    WITH staging_campanhas AS (
        SELECT DISTINCT
            2 AS sk_plataforma,
            CAST(Campaign__Campaign_Id AS STRING) AS id_campanha_original,
            Campaign__Campaign_name AS nm_campanha,
            Campaign__Campaign_status AS ds_status_campanha,
            CAST(NULL AS STRING) AS ds_objetivo_campanha,
            CAST(NULL AS DATE) AS dt_inicio_campanha
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.googleads_campaigns`
        WHERE Campaign__Campaign_Id IS NOT NULL
        AND DATE(Row_Updated_At) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            1 AS sk_plataforma,
            CAST(id AS STRING) AS id_campanha_original,
            name AS nm_campanha,
            status AS ds_status_campanha,
            CAST(objective AS STRING) AS ds_objetivo_campanha,
            SAFE_CAST(start_time AS DATE) AS dt_inicio_campanha
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.metaads_campaigns`
        WHERE id IS NOT NULL
        AND DATE(Row_Updated_At) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            4 AS sk_plataforma,
            REGEXP_EXTRACT(CAST(Campaign__Campaign_Id AS STRING), r'(\d+)') AS id_campanha_original,
            Campaign__Campaign_name AS nm_campanha,
            Campaign__Campaign_status AS ds_status_campanha,
            CAST(Campaign__Objective_type AS STRING) AS ds_objetivo_campanha,
            SAFE_CAST(Campaign__Campaign_created_at AS DATE) AS dt_inicio_campanha
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.linkedinads_campaigns`
        WHERE Campaign__Campaign_Id IS NOT NULL
        AND DATE(Row_Updated_At) = '{D_MINUS_1}'

        UNION DISTINCT

        SELECT DISTINCT
            3 AS sk_plataforma,
            CAST(CampaignId AS STRING) AS id_campanha_original,
            CampaignName AS nm_campanha,
            CampaignStatus AS ds_status_campanha,
            CAST(CampaignType AS STRING) AS ds_objetivo_campanha,
            CAST(NULL AS DATE) AS dt_inicio_campanha
        FROM `{PROJECT_ID}.{DATASET_BRONZE}.microsoftads_campaigns`
        WHERE CampaignId IS NOT NULL
        AND DATE(Row_Updated_At) = '{D_MINUS_1}'
    ),

    classificacao_taxonomia AS (
        SELECT
            sk_plataforma,
            id_campanha_original,
            nm_campanha,
            ds_status_campanha,
            ds_objetivo_campanha,
            dt_inicio_campanha,
            CASE
                WHEN LOWER(nm_campanha) = 'campanhas form' THEN 'linkedin-cpc'
                WHEN LOWER(nm_campanha) = 'conversão feed' THEN 'linkedin-cpc'
                WHEN LOWER(nm_campanha) = 'campanha de candidatos à vaga - rh' THEN 'linkedin-cpc'
                WHEN LOWER(nm_campanha) = 'linkedin-cpc-views-projetos' THEN 'linkedin-cpc'
                WHEN LOWER(nm_campanha) = 'meta-cpc-jota-evento-trabalhista-reconhecimento-evento-marketing-trabalhista' THEN 'meta-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'meta-cpc') THEN 'meta-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'google-cpc') THEN 'google-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'linkedin-cpc') THEN 'linkedin-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'bing-cpc') THEN 'bing-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'taboola-cpc') THEN 'taboola-cpc'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'whatsapp') THEN 'whatsapp'
                ELSE NULL
            END AS canal,
            CASE
                WHEN LOWER(nm_campanha) = 'campanhas form' THEN 'form'
                WHEN LOWER(nm_campanha) = 'conversão feed' THEN 'social'
                WHEN LOWER(nm_campanha) = 'campanha de candidatos à vaga - rh' THEN 'social'
                WHEN LOWER(nm_campanha) = 'linkedin-cpc-views-projetos' THEN 'social'
                WHEN LOWER(nm_campanha) = 'meta-cpc-jota-evento-trabalhista-reconhecimento-evento-marketing-trabalhista' THEN 'social'
                WHEN LOWER(nm_campanha) = 'google-cpc-dem-gem-conversao' THEN 'dem-gem'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'social') THEN 'social'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'search') THEN 'search'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'message') THEN 'message'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'taboola') THEN 'taboola'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'pmax') THEN 'pmax'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'video') THEN 'video'
                ELSE NULL
            END AS tipo,
            CASE
                WHEN LOWER(nm_campanha) = 'campanhas form' THEN 'lead'
                WHEN LOWER(nm_campanha) = 'conversão feed' THEN 'trafego'
                WHEN LOWER(nm_campanha) = 'campanha de candidatos à vaga - rh' THEN 'rh'
                WHEN LOWER(nm_campanha) = 'linkedin-cpc-views-projetos' THEN 'projeto'
                WHEN LOWER(nm_campanha) = 'meta-cpc-jota-evento-trabalhista-reconhecimento-evento-marketing-trabalhista' THEN 'impulsionamento'
                WHEN LOWER(nm_campanha) = 'meta-cpc-social-ad-view' THEN 'video'
                WHEN LOWER(nm_campanha) = 'meta-cpc-social-conversao-estudio-jota-abo' THEN 'projeto'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'projeto') THEN 'projeto'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'trafego') THEN 'trafego'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'conversao') THEN 'conversao'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'engajamento') THEN 'engajamento'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'impulsionamento') THEN 'impulsionamento'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'lead') THEN 'lead'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'material-rico') THEN 'material-rico'
                ELSE NULL
            END AS objetivo,
            CASE
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'bofu|conversao|pmax|dem-gem') THEN 'bofu'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'mofu|lead|engajamento|material-rico|form|message|rh') THEN 'mofu'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'tofu|trafego|impulsionamento|views|projeto') THEN 'tofu'
                ELSE NULL
            END AS funil,
            CASE
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'generica') THEN 'generica'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'institucional') THEN 'institucional'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'bofu|conversao|pmax|dem-gem') THEN 'bofu'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'mofu|lead|engajamento|material-rico|form|message|rh') THEN 'mofu'
                WHEN REGEXP_CONTAINS(LOWER(nm_campanha), r'tofu|trafego|impulsionamento|views|projeto') THEN 'tofu'
                ELSE NULL
            END AS dif
        FROM staging_campanhas
    )

    SELECT
        TO_HEX(MD5(CONCAT(CAST(sk_plataforma AS STRING), '||', id_campanha_original))) AS sk_campanha,
        sk_plataforma,
        id_campanha_original,
        nm_campanha,
        ds_status_campanha,
        ds_objetivo_campanha,
        dt_inicio_campanha,
        canal,
        tipo,
        objetivo,
        dif,
        funil,
        NULLIF(ARRAY_TO_STRING([canal, tipo, objetivo, dif], '-'), '') AS campanha_tratada
    FROM classificacao_taxonomia
) S
ON T.sk_campanha = S.sk_campanha

WHEN MATCHED THEN
    UPDATE SET
        T.nm_campanha        = S.nm_campanha,
        T.ds_status_campanha = S.ds_status_campanha,
        T.ds_objetivo_campanha = COALESCE(S.ds_objetivo_campanha, T.ds_objetivo_campanha),
        T.canal              = S.canal,
        T.tipo               = S.tipo,
        T.objetivo           = S.objetivo,
        T.dif                = S.dif,
        T.funil              = S.funil,
        T.campanha_tratada   = S.campanha_tratada

WHEN NOT MATCHED THEN
    INSERT (sk_campanha, sk_plataforma, id_campanha_original, nm_campanha, ds_status_campanha, ds_objetivo_campanha, dt_inicio_campanha, canal, tipo, objetivo, dif, funil, campanha_tratada)
    VALUES (S.sk_campanha, S.sk_plataforma, S.id_campanha_original, S.nm_campanha, S.ds_status_campanha, S.ds_objetivo_campanha, S.dt_inicio_campanha, S.canal, S.tipo, S.objetivo, S.dif, S.funil, S.campanha_tratada);

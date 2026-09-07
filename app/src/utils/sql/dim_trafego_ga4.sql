MERGE INTO `{PROJECT_ID}.{DATASET_SILVER}.{TABLE_DIM_TRAFEGO_GA4}` T
USING (
    SELECT
        traffic_sk,
        source,
        medium,
        campaign,
        traffic_group,
        origem_ga4,
        source_medium
    FROM `{PROJECT_ID}.{DATASET_GA4}.vw_dTraffic`
) S
ON T.traffic_sk = S.traffic_sk

WHEN MATCHED THEN
    UPDATE SET
        T.source        = S.source,
        T.medium        = S.medium,
        T.campaign      = S.campaign,
        T.traffic_group = S.traffic_group,
        T.origem_ga4    = S.origem_ga4,
        T.source_medium = S.source_medium

WHEN NOT MATCHED THEN
    INSERT (traffic_sk, source, medium, campaign, traffic_group, origem_ga4, source_medium)
    VALUES (S.traffic_sk, S.source, S.medium, S.campaign, S.traffic_group, S.origem_ga4, S.source_medium);

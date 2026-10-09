-- We build Silver on top of the snapshot to get the cleanest active records
WITH guests_scd2 AS (
    SELECT * FROM {{ ref('snp_hotel_guests') }}
)

SELECT
    CAST(legacy_hotel_id AS STRING) AS hotel_id,
    CAST(first_name AS STRING) AS first_name,
    CAST(last_name AS STRING) AS last_name,
    CAST(email AS STRING) AS email,
    CAST(tier AS STRING) AS current_tier
FROM guests_scd2
-- We only expose the currently active tier to the daily pipeline
WHERE dbt_valid_to IS NULL
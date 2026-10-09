{{ config(
    materialized='table',
    cluster_by=['global_guest_sk']
) }}

WITH identity AS (
    -- Brings in our unified Surrogate Key (SK) and bridge logic
    SELECT * FROM {{ ref('int_guest_identity') }}
),
guest_history AS (
    -- Brings in the SCD Type 2 history from our dbt snapshot
    SELECT * FROM {{ ref('snp_hotel_guests') }}
)

SELECT
    i.global_guest_sk,
    i.casino_account_id,
    h.legacy_hotel_id,
    h.first_name,
    h.last_name,
    h.email,
    h.tier AS loyalty_tier,
    h.dbt_valid_from AS valid_from_ts,
    h.dbt_valid_to AS valid_to_ts,
    -- Creates a simple boolean flag for BI dashboards to easily filter active status
    CASE
        WHEN h.dbt_valid_to IS NULL THEN TRUE
        ELSE FALSE
    END AS is_current_record
FROM identity i
-- We join back to the snapshot to inherit the historical tier records
LEFT JOIN guest_history h
    ON i.legacy_hotel_id = h.legacy_hotel_id
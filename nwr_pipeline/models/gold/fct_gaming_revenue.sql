{{ config(
    materialized='incremental',
    unique_key='transaction_id',
    incremental_strategy='merge',
    cluster_by=['transaction_date']
) }}

WITH spins AS (
    SELECT * FROM {{ ref('slv_casino_spins') }}

    {% if is_incremental() %}
        -- LATE-ARRIVING DATA FIX: Look back 3 days to catch offline slot machines
        WHERE transaction_ts >= TIMESTAMP_SUB(
            (SELECT MAX(transaction_ts) FROM {{ this }}),
            INTERVAL 3 DAY
        )
    {% endif %}
),
identity AS (
    SELECT * FROM {{ ref('int_guest_identity') }}
)

SELECT
    spins.transaction_id,
    identity.global_guest_sk,
    spins.wager_amount,
    spins.win_amount,
    (spins.wager_amount - spins.win_amount) AS net_revenue,
    DATE(spins.transaction_ts) AS transaction_date,
    spins.transaction_ts
FROM spins
LEFT JOIN identity
    ON spins.raw_player_id = identity.casino_account_id
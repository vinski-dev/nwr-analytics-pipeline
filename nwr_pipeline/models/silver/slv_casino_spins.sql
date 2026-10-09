WITH raw_spins AS (
    SELECT * FROM {{ source('bronze', 'raw_casino_spins') }}
)

SELECT
    CAST(transaction_id AS STRING) AS transaction_id,
    CAST(player_id AS STRING) AS raw_player_id,
    CAST(wager_amount AS NUMERIC) AS wager_amount,
    CAST(win_amount AS NUMERIC) AS win_amount,
    CAST(transaction_ts AS TIMESTAMP) AS transaction_ts,
    CURRENT_TIMESTAMP() AS loaded_at
FROM raw_spins
-- PRODUCTION DEDUPLICATION: We only take the latest record per transaction_id
WHERE transaction_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_ts DESC) = 1
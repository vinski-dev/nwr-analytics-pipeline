WITH hotel_guests AS (
    SELECT * FROM {{ ref('slv_hotel_guests') }}
),
casino_spins AS (
    -- Get distinct player IDs from the casino floor
    SELECT DISTINCT raw_player_id FROM {{ ref('slv_casino_spins') }}
)

SELECT
    -- MD5 Hash generates a permanent, stable ID for the data warehouse
    {{ dbt_utils.generate_surrogate_key(['COALESCE(c.raw_player_id, h.hotel_id)']) }} AS global_guest_sk,

    c.raw_player_id AS casino_account_id,
    h.hotel_id AS legacy_hotel_id,
    h.first_name,
    h.last_name,
    h.current_tier
FROM casino_spins c
-- We use a LEFT JOIN because anonymous walk-up players won't have a hotel profile
LEFT JOIN hotel_guests h
    ON c.raw_player_id = h.hotel_id
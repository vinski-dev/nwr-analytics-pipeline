{% snapshot snp_hotel_guests %}

{{
    config(
      target_schema='bronze',
      unique_key='legacy_hotel_id',
      strategy='timestamp',
      updated_at='updated_at'
    )
}}

SELECT *
FROM {{ source('bronze', 'raw_hotel_guests') }}

{% endsnapshot %}
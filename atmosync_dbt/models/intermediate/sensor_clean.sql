SELECT
    container_id,
    commodity_type,
    timestamp,
    temperature_c,
    humidity_pct,
    gps_lat,
    gps_lon,
    anomaly,

    CASE
        WHEN temperature_c > 6 THEN 'ALERT'
        ELSE 'NORMAL'
    END AS temperature_status

FROM {{ ref('stg_sensor_data') }}
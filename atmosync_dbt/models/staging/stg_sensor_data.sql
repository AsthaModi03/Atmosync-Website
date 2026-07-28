SELECT
    timestamp,
    container_id,
    commodity_type,
    temperature_c,
    humidity_pct,
    gps_lat,
    gps_lon,
    reading_id,
    anomaly
FROM {{ source('raw', 'RAW_SENSOR_DATA') }}
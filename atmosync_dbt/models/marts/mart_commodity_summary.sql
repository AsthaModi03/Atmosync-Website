SELECT

commodity_type,

AVG(temperature_c) AS avg_temperature,

AVG(humidity_pct) AS avg_humidity,

COUNT(*) AS total_readings,

SUM(CASE WHEN anomaly THEN 1 ELSE 0 END) AS anomalies

FROM {{ ref('sensor_clean') }}

GROUP BY commodity_type
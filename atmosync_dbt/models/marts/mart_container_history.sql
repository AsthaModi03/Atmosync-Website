SELECT

container_id,

commodity_type,

AVG(temperature_c) AS avg_temperature,

MAX(temperature_c) AS max_temperature,

MIN(temperature_c) AS min_temperature,

COUNT(*) AS total_readings

FROM {{ ref('sensor_clean') }}

GROUP BY

container_id,

commodity_type
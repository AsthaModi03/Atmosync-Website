SELECT

s.container_id,
s.commodity_type,
s.timestamp,
s.temperature_c,
s.humidity_pct,
s.temperature_status,
p.price_per_kg

FROM {{ ref('sensor_clean') }} s

LEFT JOIN {{ ref('commodity_prices') }} p

ON s.commodity_type = p.commodity_type
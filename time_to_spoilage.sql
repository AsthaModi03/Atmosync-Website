{{
    config(
        materialized='table'
    )
}}

/*
    Time-to-Spoilage model
    -----------------------
    Logic: every commodity has an ideal temp/humidity band and a base
    shelf life (hours) if held perfectly inside that band. Every degree
    (or humidity point) a container drifts outside the band accelerates
    decay, modeled as a linear degradation multiplier:

        degradation_factor   = 1 + (temp_deviation   * temp_spoilage_rate_per_degree)
                                  + (humidity_deviation * humidity_spoilage_rate_per_pct)

        remaining_shelf_life_hours = base_shelf_life_hours / degradation_factor

    Spoilage % so far = hours_elapsed / remaining_shelf_life_hours, capped at 100%.
    We use the container's *average* exposure (not just the latest single
    reading) so a single momentary sensor blip doesn't dominate the estimate,
    but we also report worst-case (max) deviation for risk classification.
*/

with container_state as (

    select * from {{ ref('int_container_latest_state') }}

),

reference as (

    select * from {{ ref('spoilage_reference') }}

),

joined as (

    select
        cs.container_id,
        cs.commodity_type,
        cs.first_reading_ts,
        cs.latest_reading_ts,
        cs.hours_elapsed,
        cs.current_temperature_c,
        cs.current_humidity_pct,
        cs.current_gps_lat,
        cs.current_gps_lon,
        cs.avg_temperature_c,
        cs.max_temperature_c,
        cs.min_temperature_c,
        cs.avg_humidity_pct,
        cs.anomaly_reading_count,
        cs.total_valid_readings,
        r.ideal_temp_min_c,
        r.ideal_temp_max_c,
        r.ideal_humidity_min_pct,
        r.ideal_humidity_max_pct,
        r.base_shelf_life_hours,
        r.temp_spoilage_rate_per_degree,
        r.humidity_spoilage_rate_per_pct
    from container_state cs
    inner join reference r
        on cs.commodity_type = r.commodity_type

),

deviations as (

    select
        *,
        -- average-exposure deviation, used for the spoilage % estimate
        greatest(0, avg_temperature_c - ideal_temp_max_c)
            + greatest(0, ideal_temp_min_c - avg_temperature_c)              as avg_temp_deviation_c,
        greatest(0, avg_humidity_pct - ideal_humidity_max_pct)
            + greatest(0, ideal_humidity_min_pct - avg_humidity_pct)         as avg_humidity_deviation_pct,

        -- worst single-reading deviation seen so far, used for risk level
        greatest(
            greatest(0, max_temperature_c - ideal_temp_max_c),
            greatest(0, ideal_temp_min_c - min_temperature_c)
        ) as peak_temp_deviation_c
    from joined

),

degradation as (

    select
        *,
        1 + (avg_temp_deviation_c * temp_spoilage_rate_per_degree)
          + (avg_humidity_deviation_pct * humidity_spoilage_rate_per_pct)     as degradation_factor
    from deviations

),

spoilage_calc as (

    select
        *,
        base_shelf_life_hours / nullif(degradation_factor, 0)                 as remaining_shelf_life_hours,
        least(
            100.0,
            round(
                100.0 * hours_elapsed
                / nullif(base_shelf_life_hours / nullif(degradation_factor, 0), 0),
                2
            )
        )                                                                     as spoilage_pct
    from degradation

)

select
    container_id,
    commodity_type,
    first_reading_ts,
    latest_reading_ts,
    hours_elapsed,
    current_temperature_c,
    current_humidity_pct,
    current_gps_lat,
    current_gps_lon,
    avg_temperature_c,
    avg_humidity_pct,
    avg_temp_deviation_c,
    avg_humidity_deviation_pct,
    peak_temp_deviation_c,
    anomaly_reading_count,
    total_valid_readings,
    degradation_factor,
    round(remaining_shelf_life_hours, 1)   as remaining_shelf_life_hours,
    coalesce(spoilage_pct, 0)              as spoilage_pct,
    case
        when coalesce(spoilage_pct, 0) >= 90 then 'Critical'
        when coalesce(spoilage_pct, 0) >= 70 then 'High'
        when coalesce(spoilage_pct, 0) >= 40 then 'Medium'
        else 'Low'
    end                                     as risk_level
from spoilage_calc

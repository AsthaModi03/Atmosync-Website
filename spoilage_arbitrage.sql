{{
    config(
        materialized='table'
    )
}}

/*
    Spoilage Arbitrage model
    -------------------------
    For every container, evaluate every market that trades its commodity:

        transit_hours          = great_circle_distance(container, market) / avg_transport_speed
        projected_spoilage_pct = spoilage already accrued + (transit_hours / remaining_shelf_life)
        effective_yield        = 1 - projected_spoilage_pct   (fraction of load still sellable on arrival)
        revenue                = price_per_unit * effective_yield * quantity_units
        transport_cost         = distance_km * transport_cost_per_unit_per_km * quantity_units
        profit                 = revenue - transport_cost

    The "arbitrage" is the gain from *diverting* the shipment to the best
    market instead of dumping it at its origin market immediately (zero
    transit, zero transit spoilage, zero transport cost, but a lower price).
    Estimated Profit = best_market_profit - origin_sell_now_profit.
*/

with spoilage as (

    select * from {{ ref('time_to_spoilage') }}

),

metadata as (

    select * from {{ ref('container_metadata') }}

),

markets as (

    select * from {{ ref('market_price_data') }}

),

candidate_markets as (

    select
        s.container_id,
        s.commodity_type,
        s.risk_level,
        s.spoilage_pct,
        s.remaining_shelf_life_hours,
        s.current_gps_lat,
        s.current_gps_lon,
        m.market_id,
        m.market_name,
        m.price_per_unit,
        m.avg_transport_speed_kmh,
        m.transport_cost_per_unit_per_km,
        cm.quantity_units,
        cm.origin_market_id,

        {{ haversine_distance_km('s.current_gps_lat', 's.current_gps_lon', 'm.gps_lat', 'm.gps_lon') }}
            as distance_km

    from spoilage s
    inner join metadata cm
        on s.container_id = cm.container_id
    inner join markets m
        on s.commodity_type = m.commodity_type

),

evaluated as (

    select
        *,
        distance_km / nullif(avg_transport_speed_kmh, 0)   as transit_hours,

        -- spoilage already accrued, plus what accrues during the transit window
        least(
            100.0,
            spoilage_pct
                + 100.0 * (distance_km / nullif(avg_transport_speed_kmh, 0))
                          / nullif(remaining_shelf_life_hours, 0)
        )                                                    as projected_spoilage_pct_at_arrival

    from candidate_markets

),

economics as (

    select
        *,
        greatest(0, 1 - projected_spoilage_pct_at_arrival / 100.0) as effective_yield,
        distance_km * transport_cost_per_unit_per_km * quantity_units as transport_cost
    from evaluated

),

profit_calc as (

    select
        *,
        (price_per_unit * effective_yield * quantity_units) as revenue,
        (price_per_unit * effective_yield * quantity_units) - transport_cost as profit
    from economics

),

ranked_markets as (

    select
        *,
        row_number() over (
            partition by container_id
            order by profit desc
        ) as profit_rank
    from profit_calc

),

best_market as (

    select *
    from ranked_markets
    where profit_rank = 1

),

-- baseline: sell the load right now at its origin market (no transit, no
-- transit spoilage, no transport cost, just whatever price it fetches today)
origin_baseline as (

    select
        pc.container_id,
        pc.profit as origin_sell_now_profit
    from profit_calc pc
    where pc.market_id = pc.origin_market_id

)

select
    bm.container_id                                 as container_id,
    bm.risk_level                                   as risk_level,
    bm.spoilage_pct                                 as spoilage_pct,
    bm.market_name                                  as recommended_market,
    round(
        bm.profit - coalesce(ob.origin_sell_now_profit, 0),
        2
    )                                                as estimated_profit,

    -- supporting detail, useful for drill-down / audit but not part of the
    -- required 5-column output above
    bm.commodity_type,
    bm.market_id                as recommended_market_id,
    round(bm.distance_km, 1)    as distance_to_market_km,
    round(bm.transit_hours, 1)  as transit_hours,
    round(bm.projected_spoilage_pct_at_arrival, 2) as projected_spoilage_pct_at_arrival,
    round(bm.effective_yield, 3)   as effective_yield,
    round(bm.revenue, 2)           as projected_revenue,
    round(bm.transport_cost, 2)    as projected_transport_cost,
    round(bm.profit, 2)            as recommended_market_profit,
    round(coalesce(ob.origin_sell_now_profit, 0), 2) as origin_sell_now_profit
from best_market bm
left join origin_baseline ob
    on bm.container_id = ob.container_id
order by estimated_profit desc

with orders as (

    select * from {{ ref('stg_orders') }}

),

returns as (

    select * from {{ ref('stg_returns') }}

),

people as (

    select * from {{ ref('stg_people') }}

),

enriched as (

    select
        -- keys
        o.row_id,
        o.order_id,
        o.customer_id,
        o.product_id,

        -- dates
        o.order_date,
        o.ship_date,
        datediff('day', o.order_date, o.ship_date)  as days_to_ship,

        -- customer
        o.customer_name,
        o.segment,

        -- geography
        o.country,
        o.city,
        o.state,
        o.postal_code,
        o.region,

        -- manager (left join — 4 regions, always matches)
        p.manager_name,

        -- product
        o.category,
        o.sub_category,
        o.product_name,
        o.ship_mode,

        -- financials
        o.sales,
        o.quantity,
        o.discount,
        o.discount_pct,
        o.profit,
        round(
            o.profit / nullif(o.sales, 0),
            4
        )                                           as profit_margin,

        -- returns (left join — nulls become false)
        coalesce(r.is_returned, false)              as is_returned

    from orders o
    left join returns r on o.order_id = r.order_id
    left join people  p on o.region   = p.region

)

select * from enriched
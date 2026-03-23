with orders as (

    select * from {{ ref('fct_orders') }}

),

summary as (

    select
        date_trunc('month', order_date)     as order_month,
        region,
        manager_name,
        segment,
        category,

        count(distinct order_id)            as total_orders,
        sum(quantity)                       as total_units,
        round(sum(sales), 2)                as total_revenue,
        round(sum(profit), 2)               as total_profit,
        round(sum(profit) / nullif(sum(sales), 0), 4) as profit_margin

    from orders

    group by 1, 2, 3, 4, 5

)

select * from summary
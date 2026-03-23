with orders as (

    select * from {{ ref('fct_orders') }}

)

select
    order_id,
    product_name,
    category,
    sub_category,
    region,
    segment,
    sales,
    profit,
    discount,
    discount_pct,
    quantity,
    round(profit / nullif(sales, 0) * 100, 2)  as profit_margin_pct,
    case
        when discount = 0         then 'No discount'
        when discount <= 0.10     then '1–10%'
        when discount <= 0.20     then '11–20%'
        when discount <= 0.30     then '21–30%'
        else '30%+'
    end                                          as discount_tier

from orders
with orders as (

    select * from {{ ref('int_orders_enriched') }}

),

products as (

    select distinct
        product_id,
        product_name,
        category,
        sub_category

    from orders

)

select * from products
with orders as (

    select * from {{ ref('int_orders_enriched') }}

),

customers as (

    select distinct
        customer_id,
        customer_name,
        segment

    from orders

)

select * from customers
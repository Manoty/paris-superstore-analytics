with orders as (

    select * from {{ ref('int_orders_enriched') }}

),

geography as (

    select distinct
        city,
        state,
        region,
        postal_code,
        country,
        manager_name

    from orders

)

select * from geography
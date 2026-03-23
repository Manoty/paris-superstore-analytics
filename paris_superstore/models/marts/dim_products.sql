with orders as (

    select * from {{ ref('int_orders_enriched') }}

),

products as (

    select
        product_id,
        product_name,
        category,
        sub_category,
        row_number() over (
            partition by product_id
            order by count(*) desc
        ) as rn

    from orders
    group by 1, 2, 3, 4

),

deduped as (

    select
        product_id,
        product_name,
        category,
        sub_category

    from products
    where rn = 1

)

select * from deduped
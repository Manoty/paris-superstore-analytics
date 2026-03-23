with orders as (

    select * from {{ ref('int_orders_enriched') }}

),

-- count occurrences of each full product combination
product_counts as (

    select
        product_id,
        product_name,
        category,
        sub_category,
        count(*) as occurrences

    from orders
    group by 1, 2, 3, 4

),

-- rank combinations per product_id, most frequent wins
ranked as (

    select
        product_id,
        product_name,
        category,
        sub_category,
        row_number() over (
            partition by product_id
            order by occurrences desc
        ) as rn

    from product_counts

),

deduped as (

    select
        product_id,
        product_name,
        category,
        sub_category

    from ranked
    where rn = 1

)

select * from deduped
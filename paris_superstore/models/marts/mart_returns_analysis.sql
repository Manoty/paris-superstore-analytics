with orders as (

    select * from {{ ref('fct_orders') }}

),

analysis as (

    select
        region,
        category,
        sub_category,
        segment,

        count(*)                                        as total_lines,
        count(distinct order_id)                        as total_orders,
        sum(case when is_returned then 1 else 0 end)    as returned_lines,
        round(
            sum(case when is_returned then 1 else 0 end)
            / nullif(count(*), 0)::double
        , 4)                                            as return_rate,
        round(sum(case when is_returned
            then profit else 0 end), 2)                 as profit_lost_to_returns

    from orders

    group by 1, 2, 3, 4

)

select * from analysis
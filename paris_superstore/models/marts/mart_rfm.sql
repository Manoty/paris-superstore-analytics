with orders as (

    select * from {{ ref('fct_orders') }}

),

rfm_base as (

    select
        customer_id,
        customer_name,
        segment,
        region,

        -- recency: days since last order
        datediff('day', max(order_date), current_date)  as recency_days,

        -- frequency: number of distinct orders
        count(distinct order_id)                         as frequency,

        -- monetary: total spend
        round(sum(sales), 2)                             as monetary

    from orders
    group by 1, 2, 3, 4

),

scored as (

    select *,
        ntile(5) over (order by recency_days desc)  as r_score,
        ntile(5) over (order by frequency asc)      as f_score,
        ntile(5) over (order by monetary asc)       as m_score

    from rfm_base

),

segmented as (

    select *,
        r_score + f_score + m_score                  as rfm_total,
        case
            when r_score >= 4 and f_score >= 4       then 'Champions'
            when r_score >= 3 and f_score >= 3       then 'Loyal customers'
            when r_score >= 4 and f_score < 2        then 'New customers'
            when r_score >= 3 and f_score < 3        then 'Potential loyalists'
            when r_score < 3 and f_score >= 3        then 'At risk'
            when r_score < 2 and f_score < 2         then 'Lost'
            else 'Needs attention'
        end                                          as rfm_segment

    from scored

)

select * from segmented
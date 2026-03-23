{{
    config(
        materialized = 'incremental',
        unique_key   = 'row_id'
    )
}}

with enriched as (

    select * from {{ ref('int_orders_enriched') }}

    {% if is_incremental() %}
        where order_date > (select max(order_date) from {{ this }})
    {% endif %}

)

select * from enriched
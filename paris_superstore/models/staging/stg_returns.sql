with source as (

    select * from {{ source('superstore_raw', 'returns') }}

),

renamed as (

    select
        "Order ID"                                      as order_id,
        "Returned"::boolean                             as is_returned                                            as is_returned

    from source

)

select * from renamed
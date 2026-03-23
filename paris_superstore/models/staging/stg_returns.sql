with source as (

    select * from {{ source('superstore_raw', 'returns') }}

),

renamed as (

    select
        "Order ID"                                      as order_id,
        case
            when upper(trim("Returned")) = 'YES' then true
            else false
        end                                             as is_returned

    from source

)

select * from renamed
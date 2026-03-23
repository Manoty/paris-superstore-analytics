with source as (

    select * from {{ source('superstore_raw', 'people') }}

),

renamed as (

    select
        "Person"    as manager_name,
        "Region"    as region

    from source

)

select * from renamed
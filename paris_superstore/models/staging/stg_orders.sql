with source as (

    select * from {{ source('superstore_raw', 'orders') }}

),

renamed as (

    select
        "Row ID"                                        as row_id,
        "Order ID"                                      as order_id,
        "Customer ID"                                   as customer_id,
        "Product ID"                                    as product_id,

        strptime("Order Date", '%m/%d/%Y')::date        as order_date,
        strptime("Ship Date",  '%m/%d/%Y')::date        as ship_date,

        "Customer Name"                                 as customer_name,
        "Segment"                                       as segment,

        "Country"                                       as country,
        "City"                                          as city,
        "State"                                         as state,
        lpad(cast("Postal Code" as varchar), 5, '0')    as postal_code,
        "Region"                                        as region,

        "Ship Mode"                                     as ship_mode,

        "Category"                                      as category,
        "Sub-Category"                                  as sub_category,
        "Product Name"                                  as product_name,

        cast("Sales"    as double)                      as sales,
        cast("Quantity" as integer)                     as quantity,
        cast("Discount" as double)                      as discount,
        cast("Discount" as double) * 100                as discount_pct,
        cast("Profit"   as double)                      as profit

    from source

)

select * from renamed
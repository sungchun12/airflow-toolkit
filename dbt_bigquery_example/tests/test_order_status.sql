-- If >= 50% of order statuses are NOT completed, then the test returns 1 row (failure)
-- If < 50% of order statuses are Not completed, then the test returns 0 rows (success)

{{ config(severity='warn') }}

with calc as (

    select
        case
            when status != "completed" then 1
            else 0
        end as status_flag
  
    from {{ ref('fct_orders') }}
  
),

agg as (
  
    select
        cast(sum(status_flag) as FLOAT64) / nullif(count(*), 0) as pct_not_completed

    from calc

)

select *
from agg
where pct_not_completed > 0.50
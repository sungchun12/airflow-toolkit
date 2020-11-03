/*
  This snapshot table will live in:
    analytics.snapshots.orders_snapshot
  Run with below command:
    dbt snapshot

  https://github.com/fishtown-analytics/dbt/issues/1599#issuecomment-510528614
*/


{% snapshot orders_snapshot %}

    {{
        config
(
          target_schema='dbt_bq_example',
          unique_key='id',
          
          strategy='check',
          check_cols=['status'],
        )
    }}

-- Pro-Tip: Use sources in snapshots!
select * from {{ source('dbt_bq_example','raw_orders') }}
    
{% endsnapshot %}

select
    id as customer_id,
    upper(country) as country,
    created_at
from {{ ref('customers') }}
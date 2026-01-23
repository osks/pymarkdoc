{% if and(true, not(false)) %}Yes{% /if %}
Equals: {% equals(1, 1, 1) %}
Default: {% default($missing, "ok") %}

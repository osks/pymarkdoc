{% if and(true, not(false)) %}Yes{% /if %}{% if equals(1, 1, 1) %}Equals{% /if %}{% if default($flag, true) %}Default{% /if %}

Debug: {% debug($data) %}

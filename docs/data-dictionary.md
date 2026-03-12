# Data Dictionary

## `operators`

| Field | Type | Description |
| --- | --- | --- |
| `id` | Integer | Internal primary key |
| `noc` | String | National Operator Code from BODS |
| `name` | String | Operator display name |
| `region` | String | Region label, fixed to `Leeds` for this project |

## `routes`

| Field | Type | Description |
| --- | --- | --- |
| `id` | Integer | Internal primary key |
| `operator_id` | Integer | Foreign key to `operators.id` |
| `route_code` | String | Public route code |
| `route_name` | String | Route label or line name |
| `origin` | String | Start location |
| `destination` | String | End location |

## `stops`

| Field | Type | Description |
| --- | --- | --- |
| `id` | Integer | Internal primary key |
| `stop_code` | String | Stop code extracted from BODS |
| `stop_name` | String | Stop display name |
| `locality` | String | Locality or area name |
| `latitude` | Float | Latitude |
| `longitude` | Float | Longitude |

## `route_stops`

| Field | Type | Description |
| --- | --- | --- |
| `route_id` | Integer | Foreign key to `routes.id` |
| `stop_id` | Integer | Foreign key to `stops.id` |
| `stop_sequence` | Integer | Ordered position within the route |

## `reliability_metrics`

| Field | Type | Description |
| --- | --- | --- |
| `id` | Integer | Internal primary key |
| `route_id` | Integer | Foreign key to `routes.id` |
| `metric_date` | Date | Aggregation date |
| `time_band` | String | One of `morning_peak`, `midday`, `evening_peak`, `off_peak` |
| `avg_delay_minutes` | Float | Average delay in minutes |
| `on_time_rate` | Float | Share of observations with delay <= 5 minutes |
| `cancellation_rate` | Float | Share of observations counted as cancelled |
| `observation_count` | Integer | Number of observations used for the aggregate |

## `incidents`

| Field | Type | Description |
| --- | --- | --- |
| `id` | Integer | Internal primary key |
| `title` | String | Short incident summary |
| `description` | String | Longer incident description |
| `incident_type` | String | Incident category, e.g. `delay`, `closure`, `crowding` |
| `severity` | String | One of `low`, `medium`, `high` |
| `status` | String | One of `open`, `monitoring`, `resolved` |
| `route_id` | Integer | Foreign key to `routes.id` |
| `stop_id` | Integer | Nullable foreign key to `stops.id` |
| `reported_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification timestamp |

## Derived Metrics

- `avg_delay_minutes`: mean delay across observations in the aggregation bucket
- `on_time_rate`: proportion of observations where delay is no more than `5` minutes
- `cancellation_rate`: proportion of missing or cancelled observations in the bucket
- `time_band`: fixed project enum to keep analytics queries simple and consistent

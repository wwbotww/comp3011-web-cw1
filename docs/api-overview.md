# API Overview

## Authentication Rules

- `GET` endpoints are public
- `POST`, `PUT`, and `DELETE` incident endpoints require `X-API-Key`

## Endpoints

### `GET /operators`

Returns the list of operators imported from `BODS`.

### `GET /routes`

Returns route records with optional filtering by operator or search text.

Query parameters:
- `operator_id`
- `q`
- `limit`
- `offset`

### `GET /routes/{route_id}`

Returns one route with its operator and ordered stop list.

### `GET /stops`

Returns stop records with optional text filtering.

Query parameters:
- `q`
- `limit`
- `offset`

### `POST /incidents`

Creates a new incident report for a route and optional stop.

Protected by:
- `X-API-Key`

### `GET /incidents`

Returns incidents with optional filtering.

Query parameters:
- `route_id`
- `severity`
- `status`
- `limit`
- `offset`

### `GET /incidents/{incident_id}`

Returns a single incident.

### `PUT /incidents/{incident_id}`

Updates an incident.

Protected by:
- `X-API-Key`

### `DELETE /incidents/{incident_id}`

Deletes an incident.

Protected by:
- `X-API-Key`

### `GET /analytics/routes/{route_id}/reliability`

Returns route reliability metrics for a date range and optional time band.

Query parameters:
- `start_date`
- `end_date`
- `time_band`

## Status Code Policy

- `200 OK` for successful reads and updates
- `201 Created` for incident creation
- `204 No Content` for successful deletion
- `401 Unauthorized` for missing or invalid `X-API-Key`
- `404 Not Found` for missing routes, stops, or incidents
- `422 Unprocessable Entity` for validation errors

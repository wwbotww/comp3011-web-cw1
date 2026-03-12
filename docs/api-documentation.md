# API Documentation

Leeds Bus Reliability and Delay Analytics API - endpoints, parameters, request/response formats, authentication, and error codes.

**Base URL (local):** `http://127.0.0.1:8000`

---

## 1. Authentication

- **Public (no auth):** All `GET` endpoints.
- **Protected:** `POST`, `PUT`, and `DELETE` under `/incidents` require the `X-API-Key` header.

**How to authenticate:**

Include the header in every write request:

```http
X-API-Key: your-write-api-key
```

The key is configured in `.env` as `WRITE_API_KEY`. If the header is missing or invalid, the API returns `401 Unauthorized`.

---

## 2. Error codes

| HTTP status | Meaning |
|-------------|--------|
| `200 OK` | Successful read or update. |
| `201 Created` | Incident created successfully. |
| `204 No Content` | Incident deleted successfully (no body). |
| `401 Unauthorized` | Missing or invalid `X-API-Key` on a protected endpoint. |
| `404 Not Found` | Resource not found (e.g. route, stop, incident by ID). |
| `422 Unprocessable Entity` | Validation error (invalid body or query parameters). |

---

## 3. Endpoints

### 3.1 GET /operators

Returns all operators imported from BODS.

**Parameters:** None.

**Example response (200):**

```json
[
  {
    "id": 1,
    "noc": "YKRT",
    "name": "Example Operator",
    "region": "Yorkshire"
  }
]
```

---

### 3.2 GET /routes

Returns route records with optional filters.

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| `operator_id` | integer | Filter by operator ID. |
| `q` | string | Search in route code/name. |
| `limit` | integer (1-100) | Max results (default 20). |
| `offset` | integer (>= 0) | Skip (default 0). |

**Example request:**

```http
GET /routes?operator_id=1&limit=10
```

**Example response (200):**

```json
[
  {
    "id": 1,
    "operator_id": 1,
    "route_code": "1",
    "route_name": "City Centre - Chapel Allerton",
    "origin": "City Centre",
    "destination": "Chapel Allerton"
  }
]
```

---

### 3.3 GET /routes/{route_id}

Returns one route with operator and ordered stops.

**Path parameters:** `route_id` (integer).

**Example request:**

```http
GET /routes/1
```

**Example response (200):**

```json
{
  "id": 1,
  "operator_id": 1,
  "route_code": "1",
  "route_name": "City Centre - Chapel Allerton",
  "origin": "City Centre",
  "destination": "Chapel Allerton",
  "operator": {
    "id": 1,
    "noc": "YKRT",
    "name": "Example Operator",
    "region": "Yorkshire"
  },
  "stops": [
    {
      "id": 1,
      "stop_code": "45001234",
      "stop_name": "City Square",
      "locality": "Leeds",
      "latitude": 53.796,
      "longitude": -1.548
    }
  ]
}
```

**Error:** `404 Not Found` if `route_id` does not exist.

---

### 3.4 GET /stops

Returns stop records with optional search.

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| `q` | string | Search in stop code/name/locality. |
| `limit` | integer (1-100) | Default 20. |
| `offset` | integer (>= 0) | Default 0. |

**Example request:**

```http
GET /stops?q=City&limit=5
```

**Example response (200):**

```json
[
  {
    "id": 1,
    "stop_code": "45001234",
    "stop_name": "City Square",
    "locality": "Leeds",
    "latitude": 53.796,
    "longitude": -1.548
  }
]
```

---

### 3.5 POST /incidents

Creates a new incident. **Requires `X-API-Key`.**

**Request body (JSON):**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | yes | 3-255 chars |
| `description` | string | no | max 2000 chars |
| `incident_type` | string | yes | 2-64 chars |
| `severity` | string | yes | `low`, `medium`, `high` |
| `status` | string | no | `open`, `monitoring`, `resolved` (default `open`) |
| `route_id` | integer | yes | Must exist |
| `stop_id` | integer | no | Must exist if provided |

**Example request:**

```http
POST /incidents
Content-Type: application/json
X-API-Key: your-write-api-key

{
  "title": "Delay at City Square",
  "description": "Heavy traffic",
  "incident_type": "congestion",
  "severity": "medium",
  "status": "open",
  "route_id": 1,
  "stop_id": 1
}
```

**Example response (201):**

```json
{
  "id": 1,
  "title": "Delay at City Square",
  "description": "Heavy traffic",
  "incident_type": "congestion",
  "severity": "medium",
  "status": "open",
  "route_id": 1,
  "stop_id": 1,
  "reported_at": "2025-03-11T12:00:00",
  "updated_at": null
}
```

**Errors:** `401 Unauthorized` (invalid/missing API key), `422 Unprocessable Entity` (validation), `404` if `route_id` or `stop_id` does not exist.

---

### 3.6 GET /incidents

Returns incidents with optional filters.

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| `route_id` | integer | Filter by route. |
| `severity` | string | `low`, `medium`, `high`. |
| `status` | string | `open`, `monitoring`, `resolved`. |
| `limit` | integer (1-100) | Default 20. |
| `offset` | integer (>= 0) | Default 0. |

**Example request:**

```http
GET /incidents?severity=medium&status=open
```

**Example response (200):**

```json
[
  {
    "id": 1,
    "title": "Delay at City Square",
    "description": "Heavy traffic",
    "incident_type": "congestion",
    "severity": "medium",
    "status": "open",
    "route_id": 1,
    "stop_id": 1,
    "reported_at": "2025-03-11T12:00:00",
    "updated_at": null
  }
]
```

---

### 3.7 GET /incidents/{incident_id}

Returns a single incident.

**Path parameters:** `incident_id` (integer).

**Example response (200):** Same JSON shape as one element in the list above.

**Error:** `404 Not Found` if the incident does not exist.

---

### 3.8 PUT /incidents/{incident_id}

Updates an incident. **Requires `X-API-Key`.** All body fields are optional; only provided fields are updated.

**Request body (JSON):** Same fields as POST, all optional.

**Example request:**

```http
PUT /incidents/1
Content-Type: application/json
X-API-Key: your-write-api-key

{
  "status": "resolved",
  "description": "Cleared after 20 minutes"
}
```

**Example response (200):** Full incident object (same shape as GET /incidents/{id}).

**Errors:** `401 Unauthorized`, `404 Not Found`, `422 Unprocessable Entity`.

---

### 3.9 DELETE /incidents/{incident_id}

Deletes an incident. **Requires `X-API-Key`.**

**Example request:**

```http
DELETE /incidents/1
X-API-Key: your-write-api-key
```

**Response:** `204 No Content` (no body).

**Errors:** `401 Unauthorized`, `404 Not Found`.

---

### 3.10 GET /analytics/routes/{route_id}/reliability

Returns route-level reliability metrics for a date range and optional time band.

**Path parameters:** `route_id` (integer).

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| `start_date` | string (YYYY-MM-DD) | Start of period. |
| `end_date` | string (YYYY-MM-DD) | End of period. |
| `time_band` | string | Optional filter (e.g. morning peak). |

**Example request:**

```http
GET /analytics/routes/1/reliability?start_date=2025-03-01&end_date=2025-03-10
```

**Example response (200):**

```json
{
  "route_id": 1,
  "start_date": "2025-03-01",
  "end_date": "2025-03-10",
  "time_band": null,
  "avg_delay_minutes": 2.5,
  "on_time_rate": 0.88,
  "cancellation_rate": 0.02,
  "observation_count": 150
}
```

**Error:** `404 Not Found` if the route does not exist or has no metrics.

---

## 4. Interactive documentation

When the API is running, OpenAPI (Swagger) UI is available at:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON:** `http://127.0.0.1:8000/openapi.json`

These provide the same endpoints, parameters, and schemas with try-it-out support.

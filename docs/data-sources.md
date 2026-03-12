# Data Sources

## Single External Source

This project uses `BODS` as its only external data source to reduce mapping complexity and improve consistency between imported records and computed analytics.

## Source 1: BODS Timetable API

Purpose:
- Build `operators`
- Build `routes`
- Build `stops`
- Build `route_stops`

Usage rules:
- Accessed only during offline data preparation
- Filtered to `Leeds` services where possible
- Downloads raw timetable dataset files and parses `TransXChange` XML into local CSV files before database import

Expected outputs:
- `data/processed/operators.csv`
- `data/processed/routes.csv`
- `data/processed/stops.csv`
- `data/processed/route_stops.csv`

## Source 2: BODS Vehicle Location Snapshots

Purpose:
- Generate `reliability_metrics`

Usage rules:
- Accessed only during offline data preparation
- Captured for a fixed sampling window
- Stored as raw `SIRI-VM` XML or equivalent feed response
- Joined with timetable-derived route information before aggregation

Expected output:
- `data/processed/reliability_metrics.csv`

## Why One Source

- Reduces cross-source identifier mapping
- Keeps route and stop records aligned with analytics inputs
- Makes the technical report and oral explanation clearer
- Avoids runtime dependency on third-party services

## Environment Variables

- `BODS_API_KEY`: used only by fetch scripts
- `WRITE_API_KEY`: used only by the API to protect write endpoints

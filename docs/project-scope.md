# Project Scope

## Project Definition

`Leeds Bus Reliability and Delay Analytics API` is a public-read API for bus route information and reliability summaries in `Leeds`, backed by `SQLite` and built with `FastAPI`.

## Fixed Scope

- Geographic scope: `Leeds`
- Transport mode: `Bus` only
- External data source: `BODS` only
- Storage engine: `SQLite`
- Write protection: `X-API-Key`
- Main CRUD entity: `incidents`
- Main analytics topic: `route-level reliability`

## In Scope

- Public endpoints for operators, routes, stops, incidents, and analytics
- Incident `Create / Read / Update / Delete`
- Precomputed reliability metrics stored in the database
- Offline data fetching and import scripts
- API documentation, technical documentation, and tests

## Out of Scope

- Real-time streaming endpoints
- Prediction models
- Frontend UI or mapping interface
- Multi-region support
- Rail, tram, or multimodal transport
- User accounts, JWT, or role-based permissions

## User Groups

- `Commuters`: browse routes, stops, and disruptions
- `Local analysts`: review route-level reliability summaries
- `Course examiners`: verify API design, data modeling, and implementation quality

## Quality Targets

- Clear HTTP status codes and validation behaviour
- Consistent naming between code, docs, and report
- Reproducible data preparation pipeline
- Stable local demonstration without runtime dependency on external services

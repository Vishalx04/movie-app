# 002 — Single FastAPI Service (Not Express + FastAPI)

## Status
Accepted

## Context
The original plan split the backend into an Express "core API" service
and a separate FastAPI "ML service," mirroring how larger companies
separate product backend from ML serving.

## Decision
Use a single FastAPI service for both product API routes and ML serving
routes, with an internal code boundary (`app/api/` vs `app/ml/`)
preserved so the ML router could be extracted into its own service later
without a rewrite.

## Reasoning
- This is an early-career portfolio project (not a team's fifth backend
  service) — a two-service split adds real deployment/orchestration
  complexity before the core patterns (auth, service-layer separation,
  migrations) are solid in even one service.
- The project is deliberately going deep into ML/AI work. Python depth
  compounds faster than splitting effort and context-switching across
  two languages (Express/TS + FastAPI/Python) for what would otherwise
  be one coherent product.
- FastAPI + Pydantic already gives type validation, auto-generated docs,
  and direct access to the Python ML ecosystem (pandas, scikit-learn,
  MLflow) in the same codebase the API lives in — no serialization
  boundary needed between "the API" and "the model."

## Consequences
- The `ml-service/` folder from the original repo layout is unused —
  ML code lives in `app/ml/` inside the single service instead.
- If real scale ever demands independent scaling of ML inference vs.
  product API traffic, the `app/api/` vs `app/ml/` boundary is the seam
  to split along — this was a deliberate design constraint, not an
  afterthought.
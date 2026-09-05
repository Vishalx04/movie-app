# Movie Recommendation App — Project Plan (Updated)

An IMDb-style movie app combining recommendation systems, AI automation, full-stack development, testing, and security — built as a learning project to move from tutorial-level skills toward production-style engineering practices.

This supersedes the original plan's architecture/milestone sections. See the separate living progress doc for narrative history, bugs found, and decision reasoning.

---

## 1. Concept

A movie discovery app where users browse/rate movies, track a watchlist, and get personalized recommendations across three distinct surfaces:

- **"Users with similar taste"** — pure collaborative filtering
- **"Because you liked X"** — pure content-based filtering
- **"You may like"** — hybrid, blending both signals

Built on:
- **MovieLens (`ml-20m`)** — 20M ratings, 26.7K movies, seed data for the recommender
- **TMDB API** — live metadata, posters, release dates
- **AI automation** — LLM-generated personalized release notifications (later milestone)

---

## 2. Architecture

### 2.1 Single-service backend
FastAPI handles both product API routes and ML serving routes in one codebase, not a separate Express + FastAPI split. Internal boundary (`app/api/` vs `app/ml/`) preserves the option to extract ML into its own service later without a rewrite.

**Why:** early-career project — depth in one language compounds faster than splitting effort across two, especially heading into ML-heavy work.

```
apps/api/
├── app/
│   ├── api/v1/          # routes — thin, parse → call service → return
│   ├── services/         # business logic, raises custom exceptions
│   ├── core/
│   │   ├── exceptions.py       # AppError + NotFoundError/UnauthorizedError/etc.
│   │   ├── error_handlers.py   # global exception → HTTP response mapping
│   │   ├── security.py         # hashing, JWT
│   │   ├── dependencies.py     # get_current_user, require_admin
│   │   └── config.py
│   ├── db/
│   │   ├── models.py
│   │   └── database.py
│   ├── schemas/           # Pydantic request/response contracts
│   └── ml/                # recommendation logic lives here (same service)
│       └── training/
│           └── notebooks/  # exploration — not production code
├── migrations/             # Alembic
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/seed/
│   ├── seed_movielens.py
│   └── enrich_tmdb.py
└── requirements.txt

apps/web/                   # Next.js (App Router), TypeScript, Tailwind v4
data/ml-20m/
docs/decisions/             # ADRs
```

### 2.2 Auth model
- Access tokens: short-lived JWT, in-memory client-side only
- Refresh tokens: httpOnly cookie, SHA-256 hash-stored server-side, rotated atomically on every use, revocable
- Role-based authorization (`user`/`admin`), admin promotion manual (no self-serve endpoint)
- OAuth (Google/GitHub) deferred

### 2.3 Error handling model
Custom exception hierarchy (`AppError` → `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `BusinessRuleError`, `ConflictError`), each mapped to the correct HTTP status by a global handler. Routes and services never construct `HTTPException` directly. `IntegrityError`, `RequestValidationError`, and unhandled exceptions all have dedicated global handlers with consistent client-facing error shapes.

### 2.4 Data model backbone
- `tmdb_id` is canonical for every movie; `movielens_id` is retained only for joining historical ratings
- `poster_path` sentinel (`NULL` = unenriched, `""` = confirmed unmatched, real value = enriched) gates what's publicly visible
- Seed users (`is_seed_user=true`) provide CF bootstrap data without being able to authenticate — enforced by the absence of a `user_credentials` row, not by weakening `NOT NULL` constraints

---

## 3. Database Schema

| Table | Purpose |
|---|---|
| `genres` | id, name, slug |
| `movies` | canonical movie data — tmdb_id, metadata, enrichment sentinel |
| `movie_genres` | pure junction |
| `people` | cast/crew — schema built, no routes yet |
| `movie_cast` | junction with role/billing — schema built, no routes yet |
| `platforms` / `movie_platforms` | streaming availability — schema built, no routes yet |
| `users` | identity only — email/username NOT NULL, role, is_seed_user |
| `user_credentials` | optional 1:1 — absence = cannot log in |
| `oauth_accounts` | deferred, not built |
| `refresh_tokens` | hash-stored, revocable, rotated |
| `ratings` | (user_id, movie_id) unique, 0.5–5.0 scale, upsert on re-rate |
| `watchlist_items` | (user_id, movie_id) unique, status enum, watched_at set once |

---

## 4. Tools & Skills

### Backend
FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, JWT/passlib

### ML
`scikit-surprise` (SVD collaborative filtering), pandas, precision@k/recall@k via sampled-negative evaluation (not naive test-set-only evaluation — see §6)

### Frontend
Next.js App Router, TypeScript, Tailwind v4, semantic design-token architecture

### Data
MovieLens `ml-20m`, TMDB API (rate-limit + retry + auth-failure handling)

### Testing
pytest, FastAPI `TestClient`, dedicated transactional Postgres test database (not SQLite — schema relies on Postgres-native `Enum`/`ondelete=CASCADE` behavior)

### Planned, not yet in use
Redis (caching + BullMQ, once needed), MLflow (experiment tracking), Docker/Kubernetes, GitHub Actions, LLM API (notifications)

---

## 5. Milestone Plan

### Milestone 0 — Foundations ✅
Repo structure, TMDB key, MovieLens download, Postgres setup, initial schema.

### Milestone 1 — Data Pipeline 🔄
- [x] Idempotent MovieLens loader (`seed_movielens.py`)
- [x] TMDB enrichment job (`enrich_tmdb.py`) with rate-limit/retry/auth-failure handling
- [ ] MovieLens seed-user + seed-ratings bulk scripts (schema ready, scripts not written)
- [ ] `people`/`platforms`/`movie_cast` routes
- [x] ADR: movie-id strategy

### Milestone 2 — Backend MVP ✅
Auth, movies, genres, ratings, watchlist — full CRUD, admin-gated where appropriate, custom exception hierarchy, unit + integration test coverage.

### Milestone 3 — Frontend MVP ✅
Browse (search/filter/infinite scroll), detail page, auth flow, watchlist page, working rate/watchlist actions, full design system.

### Milestone 4 — Recommendation Engine v1 🔄
- [x] Data exploration (sparsity, distribution analysis)
- [x] Filtering decision (≥5 ratings/movie)
- [x] SVD model trained, RMSE 0.786
- [ ] Proper precision@k/recall@k via sampled-negative evaluation (in progress — naive test-set-only evaluation was misleading, corrected approach underway)
- [ ] Wrap validated model as a FastAPI route
- [ ] "Users with similar taste" surface shippable once this completes

### Milestone 5 — Recommendation Engine v2 (hybrid + cold start)
- [ ] Content-based filtering (genre/metadata similarity) → "Because you liked X"
- [ ] Hybrid blend → "You may like"
- [ ] Real (non-seed) new-user cold-start handling
- [ ] MLflow experiment tracking

### Milestone 6 — AI Automation (Notifications)
Upcoming-release sync, relevance scoring, LLM-generated blurbs, delivery.

### Milestone 7 — Testing Hardening 🔄
Core unit/integration coverage already exists ahead of schedule. Remaining: coverage-gap review, TMDB mocking in tests, load testing.

### Milestone 7.5 — Adversarial Security Review *(new)*
Deliberately attack the app before hardening it: auth/session attacks, IDOR/authorization bypass, injection, brute-force/rate-limiting (known current gap on `/auth/login`), CORS, error-message leakage, dependency audit. Findings feed directly into Milestone 8.

### Milestone 8 — Containerization & CI/CD
Dockerize, Docker Compose, GitHub Actions: lint → test → **security scan** → build → push.

### Milestone 9 — Kubernetes & Observability
Local cluster deploy, Helm, Prometheus/Grafana, structured logging.

### Milestone 10 — Polish & Resume Packaging
Architecture diagram, README, demo video, technical write-up.

---

## 6. Key Methodological Notes Worth Preserving

- **RMSE alone is insufficient for recommender evaluation.** A model can predict ratings accurately while still failing to surface good top-N recommendations. Precision@k/recall@k are required — but must be evaluated against a realistic candidate pool (sampled unrated negatives), not just the small held-out test slice of already-rated items, which understates real performance and answers the wrong question.
- **Filtering decisions need validation, not assumption.** The ≥5-ratings-per-movie cutoff was chosen only after checking its actual impact on catalog size (68.6% of movies retained, 99.92% of ratings retained) — not applied blindly.
- **Safety-motivated schema constraints and business requirements can conflict — resolve by finding the real mechanism, not by weakening the constraint.** The seed-user reversal (ADR 003) is the clearest example: the actual goal ("nobody can log in as an account they don't own") was preserved through a different mechanism (no credentials row) rather than by loosening `NOT NULL`.

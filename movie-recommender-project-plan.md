# Movie Recommendation App — Project Plan

An IMDb-style movie app combining recommendation systems, AI automation, full-stack development, testing, and DevOps — built as a learning project to move from tutorial-level skills toward production-style engineering practices.

---

## 1. Concept

A movie discovery app where users browse/rate movies, get personalized recommendations, and receive **smart notifications** when a movie they'd likely want to watch releases. Built with:

- **MovieLens** dataset — seed data for the recommender (historical ratings)
- **TMDB API** — live metadata, posters, release dates, upcoming releases
- **AI automation** — LLM-generated personalized release notifications

This project is deliberately scoped as a full **product**, not just a model in a notebook — combining ML, backend, frontend, testing, and DevOps into one coherent system.

---

## 2. Why This Project (vs. a plain recommender)

A generic "MovieLens + cosine similarity" recommender is one of the most overused portfolio projects and blends into thousands of similar repos. What makes this version resume-worthy for larger companies:

- Two-stage pipeline mindset (candidate generation → ranking), which mirrors real recsys system design questions
- A real serving layer, not just offline notebooks
- Explicit cold-start handling (new users, new movies not in MovieLens)
- A production mindset: containerization, CI/CD, observability, testing
- An AI automation layer (notifications) that's genuinely useful, not just bolted on

---

## 3. High-Level Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Next.js   │─────▶│  Express Backend  │─────▶│   PostgreSQL     │
│  (Frontend) │      │   (Core API)      │      │  (users, ratings,│
└─────────────┘      └──────────────────┘      │   watchlist,     │
                              │                  │   movies)        │
                              │                  └─────────────────┘
                              ▼
                      ┌──────────────────┐
                      │  FastAPI ML       │
                      │  Service          │──────▶ Model artifacts
                      │  (Recommendations)│         (MLflow registry)
                      └──────────────────┘
                              │
                              ▼
                      ┌──────────────────┐      ┌─────────────────┐
                      │  Redis            │      │   TMDB API       │
                      │ (cache + queue)   │      │  (external)      │
                      └──────────────────┘      └─────────────────┘
                              │
                              ▼
                      ┌──────────────────┐
                      │  Worker            │
                      │ (BullMQ - sync jobs,│
                      │  notification jobs)│
                      └──────────────────┘
                              │
                              ▼
                      ┌──────────────────┐
                      │  Notification      │
                      │  Delivery (email)  │
                      │  + LLM blurb gen    │
                      └──────────────────┘
```

**Design rationale:**
- Express (core API) and FastAPI (ML) are **separate services**, mirroring how real companies split "product backend" from "ML serving." Enables independent scaling/deployment/retraining.
- Redis does double duty: cache for hot data (popular movies, computed recommendations) and backing store for BullMQ background jobs.
- The worker runs as a separate process from the API — background jobs shouldn't run inside a request/response server.

---

## 4. Repo Structure (Monorepo)

```
movie-app/
├── apps/
│   ├── web/                      # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/               # routes (App Router)
│   │   │   ├── components/
│   │   │   ├── lib/                # api client, hooks
│   │   │   └── types/
│   │   ├── public/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── api/                      # Express core backend
│   │   ├── src/
│   │   │   ├── routes/             # movies, users, ratings, watchlist
│   │   │   ├── controllers/
│   │   │   ├── services/           # business logic
│   │   │   ├── db/
│   │   │   │   ├── models/          # or schema if using an ORM
│   │   │   │   └── migrations/
│   │   │   ├── middleware/         # auth, error handling
│   │   │   ├── config/
│   │   │   └── index.ts
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── ml-service/                # FastAPI recommendation service
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── routes.py        # /recommendations/{user_id}
│   │   │   ├── models/              # model loading/inference logic
│   │   │   ├── schemas/             # Pydantic request/response models
│   │   │   └── main.py
│   │   ├── training/                # offline training scripts
│   │   │   ├── train_cf.py           # collaborative filtering
│   │   │   ├── train_content.py      # content-based
│   │   │   ├── evaluate.py           # precision@k, NDCG etc.
│   │   │   └── notebooks/            # exploration (not production code)
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── worker/                    # BullMQ background jobs
│       ├── src/
│       │   ├── jobs/
│       │   │   ├── syncTmdb.ts       # data pipeline job
│       │   │   ├── scoreReleases.ts  # relevance scoring
│       │   │   └── sendNotifications.ts
│       │   ├── queues/
│       │   └── index.ts
│       ├── Dockerfile
│       └── package.json
│
├── packages/                      # shared code across apps
│   ├── shared-types/                # TS types shared between api/web/worker
│   └── db-schema/                   # if sharing Prisma schema across services
│
├── data/                           # NOT committed except small samples
│   ├── movielens/                   # raw MovieLens files
│   └── links/                       # movieId <-> tmdbId mapping
│
├── scripts/                       # one-off / setup scripts
│   ├── seed_db.ts
│   └── etl_movielens.ts
│
├── infra/
│   ├── docker-compose.yml           # local dev: all services + postgres + redis
│   ├── k8s/
│   │   ├── base/                     # Deployments, Services, ConfigMaps
│   │   └── overlays/                 # dev/prod variants (kustomize)
│   ├── helm/                        # if you go Helm instead of raw manifests
│   └── terraform/                   # cloud provisioning (later milestone)
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # lint, test, build on PR
│       └── deploy.yml                # deploy on merge to main
│
├── docs/
│   ├── architecture.md
│   ├── api-spec.md
│   └── decisions/                   # ADRs (architecture decision records)
│
└── README.md
```

**Notable structural decisions:**
- `packages/shared-types` avoids duplicating TypeScript interfaces between `web` and `api`.
- `docs/decisions/` holds short ADRs (architecture decision records) — one per major decision (~half a page each). Genuinely underused practice that reviewers notice.
- Training scripts (`ml-service/training/`) are kept separate from serving code (`ml-service/app/`) — reflects the real production distinction between offline training and online inference.

---

## 5. Tools, Skills & Topics Needed

### Data & APIs
- REST API consumption (TMDB API — auth, pagination, rate limits)
- Data wrangling with pandas (joining MovieLens ↔ TMDB via `links.csv`)
- ETL concepts (extract, transform, load; idempotent re-runnable jobs)
- SQL (schema design, joins, indexing)

### ML / Recommendation
- Collaborative filtering (matrix factorization — ALS, SVD)
- Content-based filtering (TF-IDF or embeddings on genres/keywords/cast)
- Cold-start handling strategies
- Evaluation metrics: precision@k, recall@k, NDCG, MAP
- Libraries: `surprise` or `implicit` (CF), `scikit-learn`, `LightGBM` (ranking), optionally `sentence-transformers`
- Two-stage recsys concept (candidate generation → ranking)
- Experiment tracking (MLflow or Weights & Biases)

### AI Automation (Notifications)
- Job scheduling (cron, Celery beat, or k8s CronJobs)
- LLM API usage (Anthropic/OpenAI SDK) — prompt engineering basics
- Email/push delivery (SendGrid, Postmark, or Firebase Cloud Messaging)
- Idempotency and dedup logic

### Backend
- Express (core API) — you already know this
- REST/GraphQL API design
- Authentication (JWT, OAuth)
- Background task queues (BullMQ)
- ORM (Prisma or similar)
- Caching (Redis)

### Database
- PostgreSQL schema design
- Optional vector store (pgvector, Chroma, Pinecone) for content similarity
- Database migrations

### Frontend
- Next.js (SSR/ISR, routing, data fetching)
- React Query / TanStack Query for server state
- Tailwind CSS or a UI library
- Auth flows, protected routes

### Testing
- Unit testing (Vitest — already known)
- Integration testing (API endpoints against test DB)
- Mocking external APIs (TMDB)
- Load testing (Locust or k6)
- Coverage tooling (Codecov)

### DevOps
- Docker + Docker Compose (multi-service)
- CI/CD (GitHub Actions)
- Kubernetes basics (Deployments, Services, Ingress, ConfigMaps, Secrets)
- Helm charts
- Observability: Prometheus, Grafana, structured logging, Loki
- Secrets management
- Infra as Code (Terraform)

### General
- Git workflow, PRs, conventional commits
- OpenAPI/Swagger docs
- System design thinking (caching, read/write patterns, scale)
- README + architecture diagrams

---

## 6. Current Skill Baseline (as of starting this project)

**Already known — leverage, don't over-invest:**
- FastAPI basics (built a mental health score predictor endpoint)
- Express + Vitest (intermediate backend project experience)
- Next.js + React (frontend)
- Docker + EC2 deployment (single-container level)

**Genuinely new — where the real learning happens:**
1. Real ML engineering (evaluation metrics, experiment tracking, cold-start, hybrid models) — biggest value jump
2. Kubernetes / orchestration (vs. single-container EC2 deploys)
3. Background job processing (Celery/BullMQ) — first time building scheduled/async pipelines
4. CI/CD pipelines (GitHub Actions automation)
5. Observability (Prometheus/Grafana)
6. LLM API integration (programmatic use, not just chat)

**Suggested warm-up before diving in:** a throwaway "hello world" Kubernetes deployment, and a toy recommender with proper evaluation — so Kubernetes and real ML aren't being learned *and* debugged in production code simultaneously.

---

## 7. Milestone Plan

> Sequenced by dependency, not by time. A reasonable "v1 for resume" stopping point is after Milestone 6 (working product with ML + AI automation + frontend + backend). Milestones 7–10 push it from "good project" to "understands production systems."

### Milestone 0 — Foundations & Setup
- Repo structure (monorepo), decide and document why
- Get TMDB API key, explore endpoints, download MovieLens dataset
- Set up Postgres locally via Docker Compose
- Define initial DB schema: users, movies, ratings, watchlist

### Milestone 1 — Data Pipeline
1. **Get and understand the raw data** — download MovieLens (start with `ml-latest-small`), inspect `movies.csv`, `ratings.csv`, `tags.csv`, and critically `links.csv` (bridge to TMDB via `tmdbId`). Get TMDB API key and read current rate limits.
2. **Design the database schema** — core tables: `movies`, `users`, `ratings`, `watchlist_items` (later `notifications`). `movies` holds both MovieLens fields and TMDB enrichment fields. Use `tmdb_id` as the canonical movie ID going forward; keep `movielens_id` purely for joining historical ratings. Write as versioned migration files, not manual `CREATE TABLE`.
3. **Build the MovieLens loader** — script to bulk-insert CSVs into `movies`/`ratings`. Must be idempotent (upsert or check-before-insert) so re-running doesn't duplicate. Log counts (read/inserted/skipped).
4. **Build the TMDB linking/enrichment job** — for each `tmdb_id`, call `/movie/{id}` to populate poster, overview, release date, genres. Handle missing/deprecated IDs gracefully (log to an "unmatched movies" table instead of crashing). Respect TMDB rate limits with batching/backoff.
5. **Make the pipeline re-runnable and incremental** — only process new/changed data on re-run where possible. This pattern becomes the foundation for the Milestone 6 "sync upcoming releases" job.
6. **Verify with real queries** — confirm a single query can return title + genres + poster + overview + release date + MovieLens rating stats. Spot-check a handful of TMDB ID matches manually.
7. **Document it** — short ADR (`docs/decisions/001-movie-id-strategy.md`) explaining the `tmdb_id`-as-canonical decision and unmatched-movie handling.

**Definition of done:** one query returns a movie's title, genres, poster URL, overview, release date, and MovieLens rating stats.

### Milestone 2 — Backend MVP (no ML yet)
- Core API: list movies, movie detail, user auth, rate a movie, add to watchlist
- Build in Express (leverages existing skill)
- Write unit + integration tests as you go
- Auto-generate API docs (Swagger)

### Milestone 3 — Frontend MVP
- Browse/search movies, movie detail page, rate, watchlist
- Connect to backend API
- Basic auth flow (login/signup)
- Deploy an early working version for momentum

### Milestone 4 — Recommendation Engine v1
- Train collaborative filtering model on MovieLens (offline, notebook first)
- Evaluate with precision@k / NDCG, log results
- Wrap as its own FastAPI service: `/recommendations/{user_id}`
- Integrate into frontend as a "Recommended for you" rail

### Milestone 5 — Recommendation Engine v2 (Cold Start + Hybrid)
- Add content-based scoring for new/unrated movies
- Blend collaborative + content signals
- Handle new users (no ratings yet) with a reasonable fallback
- Track experiments in MLflow/W&B

### Milestone 6 — AI Automation: Smart Notifications
- Build "new/upcoming releases" sync job from TMDB
- Score new releases against user taste profiles
- Add relevance threshold logic (avoid spamming)
- Integrate LLM call to generate personalized blurb ("Because you loved X, you might want...")
- Wire up delivery (email via SendGrid, or in-app notification center first)

### Milestone 7 — Testing Hardening
- Fill gaps in unit/integration test coverage
- Mock external APIs (TMDB) in tests
- Load testing for recommendation and notification endpoints
- Coverage reporting in CI

### Milestone 8 — Containerization & CI/CD
- Dockerize every service
- Docker Compose for full local stack
- GitHub Actions pipeline: lint → test → build → push

### Milestone 9 — Kubernetes & Observability
- Deploy full stack to local k3s/kind cluster, then real cloud cluster if possible
- Write Helm charts
- Add Prometheus + Grafana dashboards (API latency, job success/failure, recommendation service health)
- Structured logging across services

### Milestone 10 — Polish & Resume Packaging
- Architecture diagram
- Strong README (problem, architecture, tradeoffs, what you'd do at scale)
- Demo video/GIF
- Short technical blog post or case study

---

## 8. Key Talking Points This Project Produces

- System design: notification fan-out, caching hot movies, two-stage recsys
- ML: cold start, offline evaluation, hybrid modeling, experiment tracking
- DevOps: CI/CD, container orchestration, observability
- Backend: API design, background job architecture, idempotent pipelines
- Product thinking: relevance thresholds, avoiding notification fatigue, real external API constraints (TMDB rate limits, missing data)

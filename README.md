# 🎬 CineMatch — Movie Recommender App

A full-stack, IMDb/Letterboxd-style movie discovery and recommendation platform built as a portfolio-grade engineering project. It delivers personalized movie suggestions across multiple algorithmic surfaces, combining collaborative filtering with semantic embeddings, automated background jobs for metadata sync, and AI-generated personalized notifications.

---

## ✨ Features

- **Catalog Exploration** — Search (contains-match), genre filtering, pagination, and detailed movie profiles with poster and backdrop imagery.
- **User Engagement** — Half-star precision rating system (0.5–5.0) and a three-state watchlist (`want_to_watch`, `watched`, `abandoned`) with transition timestamps.
- **Multi-Surface Recommendations:**
  - 🤝 *"Users with Similar Taste"* — Collaborative Filtering (SVD Matrix Factorization via `scikit-surprise`), Hit Rate@10 = **47.57%**, RMSE = **0.786**
  - 🎥 *"Because You Liked X"* — Content-Based Filtering (dense semantic embeddings via `all-MiniLM-L6-v2` + one-hot genre cosine similarity)
  - ⭐ *"For You"* — Hybrid blend of SVD candidates re-ranked against a user's content anchor movie
  - 🔥 *"Popular / Trending"* — IMDb Bayesian weighted rating formula for cold-start / anonymous users
- **AI Notifications** — Celery Beat scheduled jobs discover new theatrical releases via TMDB, find high-interest users via vector similarity, and generate personalized release blurbs using Groq LLM inference.

---

## 🏗️ Architecture

```
                       ┌─────────────────────────────────┐
                       │   Next.js 16 (React 19)         │
                       │   App Router · TypeScript        │
                       │   Tailwind v4 · AuthContext      │
                       └────────────────┬────────────────┘
                                        │ HTTP/JSON + httpOnly Cookie
                                        ▼
              ┌─────────────────────────────────────────────┐
              │          FastAPI Backend (Single Service)    │
              │  Transport → Service → ML / Persistence      │
              │  /auth /movies /genres /ratings              │
              │  /watchlist /recommendations /notifications  │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌────────────────────┐       ┌──────────────────────┐
   │  PostgreSQL 17     │       │   Redis 7 (Broker)   │
   │  SQLAlchemy 2.0    │       │   Celery Worker       │
   │  Alembic Migrations│       │   Celery Beat         │
   └────────────────────┘       └──────────┬───────────┘
                                           │
                          ┌────────────────┴──────────────┐
                          ▼                               ▼
               ┌──────────────────┐           ┌──────────────────┐
               │    TMDB API      │           │    Groq API      │
               │ Metadata & Sync  │           │ LLM Notifications│
               └──────────────────┘           └──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| **Backend** | FastAPI, Python, Uvicorn |
| **Database** | PostgreSQL 17, SQLAlchemy 2.0 ORM, Alembic |
| **Auth** | JWT (access) + httpOnly cookie (refresh), bcrypt, python-jose |
| **ML** | `scikit-surprise` (SVD), `sentence-transformers` (`all-MiniLM-L6-v2`), `scikit-learn` |
| **Background Jobs** | Celery + Celery Beat, Redis 7 |
| **AI / LLM** | Groq API (LLM blurb generation) |
| **External APIs** | TMDB (The Movie Database) |
| **Data** | MovieLens 20M dataset (20M ratings, 27K movies) |
| **Testing** | pytest, pytest-cov, httpx, FastAPI TestClient |
| **Infrastructure** | Docker Compose (PostgreSQL + Redis) |

---

## 📂 Project Structure

```
movie-app/
├── apps/
│   ├── api/                        # FastAPI Backend
│   │   ├── app/
│   │   │   ├── main.py             # App factory, middleware, router mount
│   │   │   ├── api/v1/             # HTTP Routers (thin transport layer)
│   │   │   │   ├── auth.py
│   │   │   │   ├── movies.py
│   │   │   │   ├── genres.py
│   │   │   │   ├── ratings.py
│   │   │   │   ├── watchlist.py
│   │   │   │   ├── recommendations.py
│   │   │   │   └── notifications.py
│   │   │   ├── core/               # Config, security, exceptions, dependencies
│   │   │   ├── db/                 # SQLAlchemy models & session management
│   │   │   ├── ml/                 # ML models, inference, training
│   │   │   │   ├── model_loader.py
│   │   │   │   ├── models/         # Serialized model artifacts (.pkl)
│   │   │   │   └── training/       # Training scripts & notebooks
│   │   │   ├── schemas/            # Pydantic request/response contracts
│   │   │   ├── services/           # Domain business logic layer
│   │   │   └── tasks/              # Celery background tasks
│   │   ├── migrations/             # Alembic versioned schema migrations
│   │   ├── tests/
│   │   │   ├── integration/        # HTTP integration tests (TestClient)
│   │   │   └── unit/               # Pure unit tests (mocked services)
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── web/                        # Next.js Frontend
│       └── src/
│           ├── app/                # App Router pages
│           ├── components/         # Reusable UI components
│           ├── context/            # AuthContext (in-memory JWT)
│           ├── hooks/              # useGuestOnly, etc.
│           ├── lib/                # Typed API client & domain methods
│           └── types/              # TypeScript interfaces & enums
├── data/
│   └── ml-20m/                     # MovieLens 20M raw CSVs
├── docs/
│   ├── progress.md                 # Living development log
│   └── decisions/                  # Architecture Decision Records (ADRs)
├── infra/
│   └── docker-compose.yml          # PostgreSQL 17 + Redis 7
└── scripts/
    └── seed/
        ├── seed_movielens.py       # Seeds movies & genres from MovieLens CSV
        └── enrich_tmdb.py          # Batch TMDB metadata enrichment
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** — for PostgreSQL and Redis
- **Python 3.11+**
- **Node.js 20+** and **npm**
- **TMDB API Key** — [get one free](https://developer.themovie.org/)
- **Groq API Key** — [get one free](https://console.groq.com/)

### 1. Start Infrastructure

```bash
cd infra
docker-compose up -d
```

This starts:
- **PostgreSQL 17** on `localhost:5432` (db: `movie_db`, user: `postgres`, pass: `postgres`)
- **Redis 7** on `localhost:6379`

### 2. Backend Setup

```bash
cd apps/api

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in your keys (see Environment Variables section below)

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs` (development mode only).

### 3. Seed Movie Data

```bash
# From apps/api directory, with venv active:

# Step 1: Seed movies and genres from MovieLens 20M
python -m scripts.seed.seed_movielens

# Step 2: Enrich with TMDB metadata (posters, descriptions, etc.)
python -m scripts.seed.enrich_tmdb
```

> **Note:** Enrichment contacts the TMDB API with a 0.5s rate-limit delay between requests. For the full ~18K movie catalog this will take some time. Progress is resumable — re-running skips already-enriched movies.

### 4. Frontend Setup

```bash
cd apps/web

npm install

# Configure environment
cp .env.local.example .env.local   # if it exists, or create manually
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

The frontend will be available at `http://localhost:3000`.

### 5. Start Background Workers (optional — for AI notifications)

```bash
# From apps/api, with venv active, in separate terminals:

# Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Celery Beat scheduler
celery -A app.core.celery_app beat --loglevel=info
```

---

## ⚙️ Environment Variables

Copy `apps/api/.env.example` to `apps/api/.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://postgres:postgres@localhost:5432/movie_db` |
| `APP_ENV` | `development` or `production` |
| `SECRET_KEY` | General app secret key |
| `JWT_SECRET_KEY` | Secret for signing JWT access tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default: `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default: `7`) |
| `TMDB_API_KEY` | Your TMDB v3 API key |
| `TMDB_BASE_URL` | `https://api.themoviedb.org/3` |
| `TMDB_IMAGE_BASE_URL` | `https://image.tmdb.org/t/p` |
| `ALLOWED_ORIGINS` | CORS origin, e.g. `http://localhost:3000` |
| `GROQ_API_KEY` | Your Groq API key for LLM notification generation |

---

## 🔐 Authentication & Security

- **Access Tokens:** Short-lived JWT (30 min), signed with `HS256`, stored **in-memory only** on the client — never in `localStorage`.
- **Refresh Tokens:** 64-byte cryptographically random tokens stored server-side as a **SHA-256 hash**. Delivered via `httpOnly`, `SameSite=Lax` cookie scoped to `/api/v1/auth`.
- **Atomic Token Rotation:** Every `/auth/refresh` call revokes the old token and issues a new one in a single database transaction. Reuse of a revoked token fails with `401`.
- **Role-Based Access Control:** `user` (default) and `admin` roles. Admin promotion via direct SQL only. Admin-gated endpoints: `POST /movies`, `POST /genres`.
- **Seed User Isolation:** MovieLens historical users (`is_seed_user=true`) have no `user_credentials` row — login is structurally impossible at the DB level.

---

## 🤖 ML & Recommendation Engine

### Collaborative Filtering (SVD)
- **Model:** Singular Value Decomposition via `scikit-surprise`
- **Training data:** MovieLens 20M, filtered to movies with ≥5 ratings (18,345 movies, 19,984,024 ratings)
- **Hyperparameters:** `n_factors=50`, `n_epochs=20`, `random_state=42`
- **Evaluation:** RMSE = **0.786** | Hit Rate@10 = **47.57%** (sampled-negative eval over 3,000 users)

### Content-Based Filtering
- **Semantic embeddings:** `all-MiniLM-L6-v2` → 384-dimensional L2-normalized vectors on movie overviews
- **Genre features:** One-hot encoded, L2-normalized
- **Combined score:** `0.6 × semantic_similarity + 0.4 × genre_similarity`
- **Caching:** Precomputed matrix serialized to `content_matrix_cache.pkl`, loaded with `@lru_cache`

### Hybrid Engine ("For You")
Requests 3× candidate pool from SVD, re-ranks against the user's highest-rated anchor movie using content similarity, then blends: `0.5 × CF_rank_score + 0.5 × content_score`

### Popularity Fallback
IMDb Bayesian weighted rating: WR = `(v / (v + m)) × R + (m / (v + m)) × C` — applied at the 60th-percentile vote-count threshold.

---

## 🧪 Testing

```bash
cd apps/api
pytest                    # run all tests
pytest --cov=app          # with coverage report
pytest tests/unit/        # unit tests only
pytest tests/integration/ # integration tests only
```

- **Unit tests** cover all service-layer business logic with mocked dependencies.
- **Integration tests** use FastAPI `TestClient` with a real `movie_db_test` PostgreSQL instance, wrapped in per-test transactions for isolation.

---

## 📈 Milestone Status

| Milestone | Status |
|---|---|
| 0 — Foundations | ✅ Done |
| 1 — Data Pipeline | ✅ Movies & genres seeded and TMDB-enriched |
| 2 — Backend MVP (auth, movies, ratings, watchlist) | ✅ Done |
| 3 — Frontend MVP (browse, detail, watchlist, auth) | ✅ Done |
| 4 — Recommendation Engine v1 (CF + content + hybrid) | ✅ Done |
| 5 — AI Automation & Notifications (Celery + Groq) | ✅ Done |
| 6 — Testing Hardening | 🔄 Core coverage done; gap review & load testing pending |
| 7 — Adversarial Security Review | ⏳ Not started |
| 8 — Containerization & CI/CD | ⏳ Not started |
| 9 — Kubernetes & Observability | ⏳ Not started |
| 10 — Polish & Resume Packaging | ⏳ Not started |

---

## 📄 Architecture Decision Records

Key design decisions are documented in [`docs/decisions/`](docs/decisions/):

- **[ADR 001](docs/decisions/001-movie-id-strategy.md)** — `tmdb_id` as the canonical movie identifier (vs. `movielens_id`)
- **[ADR 002](docs/decisions/002-single-fastapi-service.md)** — Single FastAPI service (API + ML) vs. microservices
- **[ADR 003](docs/decisions/003-seed-user-reconsideration.md)** — Seed user strategy for MovieLens bootstrap data

---

## 📜 License

This project is for portfolio and learning purposes.


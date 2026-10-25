# CineMatch / Movie Recommender App — Comprehensive Project Context

> **Context Document Version:** 1.0.0  
> **Last Synchronized:** October 2026 (Milestone 4/5/6 Active Phase)  
> **Purpose:** Single source of truth for architecture, domain logic, data models, ML pipelines, asynchronous workers, security contracts, frontend patterns, and operational runbooks across the entire codebase.

---

## Table of Contents

1. [Executive Overview & Philosophy](#1-executive-overview--philosophy)
2. [High-Level System Architecture](#2-high-level-system-architecture)
3. [Repository Structure & Code Boundaries](#3-repository-structure--code-boundaries)
4. [Architecture Decision Records (ADRs)](#4-architecture-decision-records-adrs)
5. [Data Backbone & Data Pipeline](#5-data-backbone--data-pipeline)
6. [Database Schema & Persistence Layer](#6-database-schema--persistence-layer)
7. [Authentication, Authorization & Security](#7-authentication-authorization--security)
8. [Recommendation Engine & ML Architecture](#8-recommendation-engine--ml-architecture)
9. [Background Processing & AI Notification Pipeline](#9-background-processing--ai-notification-pipeline)
10. [Backend REST API Specification](#10-backend-rest-api-specification)
11. [Frontend Architecture & Design System](#11-frontend-architecture--design-system)
12. [Testing Architecture & Quality Assurance](#12-testing-architecture--quality-assurance)
13. [Engineering Wins & Case Studies (Bugs Found & Fixed)](#13-engineering-wins--case-studies-bugs-found--fixed)
14. [Milestone Progress & Roadmap](#14-milestone-progress--roadmap)
15. [Environment Configuration & Operational Runbook](#15-environment-configuration--operational-runbook)

---

## 1. Executive Overview & Philosophy

### 1.1 Project Concept
The **Movie Recommender App** is a full-stack, IMDb/Letterboxd-style movie discovery and recommendation platform. Beyond basic CRUD browsing, it delivers personalized movie suggestions across three distinct algorithmic surfaces, combines collaborative filtering with dense semantic embeddings, runs automated background synchronization with external entertainment databases, and leverages generative AI to produce personalized notifications for new theatrical releases.

The project is built as a learning and portfolio vehicle to demonstrate **production-grade software engineering practices**:
- Rigorous separation of concerns (transport vs. service vs. ML serving vs. persistence).
- Defensive data modeling and strict database integrity.
- Resilient API design with structured global error handling.
- Real-world applied machine learning evaluated against realistic information-retrieval metrics (sampled-negative Hit Rate@10, not just rating prediction RMSE).
- Asynchronous distributed job processing with fault-tolerant backoff and rate-limit handling.
- Modern frontend UX with optimistic updates, generational infinite scroll, and semantic design tokens.

### 1.2 Core Capabilities
1. **Catalog Exploration & Discovery:** Search (contains-match), genre filtering, pagination, and detailed movie profiles with poster and backdrop media.
2. **User Engagement:** Half-star precision rating system (0.5 to 5.0) and a three-state watchlist (`want_to_watch`, `watched`, `abandoned`) with state-transition timestamp tracking (`watched_at`).
3. **Multi-Surface Recommendations:**
   - *"Users with similar taste"* — Pure Collaborative Filtering (Matrix Factorization via SVD).
   - *"Because you liked X"* — Pure Content-Based Filtering (Dense semantic embeddings via SentenceTransformers + one-hot genre cosine similarity).
   - *"For You"* — Hybrid blend combining top-N candidate scoring from SVD with content affinity against the user's highest-rated anchor movie.
   - *"Popular / Trending"* — Cold-start baseline powered by IMDb's weighted Bayesian rating formula.
4. **Asynchronous Automation & AI Notifications:** Celery Beat schedules background jobs to discover newly released movies from TMDB, enrich metadata asynchronously, detect high-interest users via vector similarity against their historical favorites, and synthesize personalized release announcements using Groq LLM inference.

---

## 2. High-Level System Architecture

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   Next.js 16 (React 19)                │
                       │     App Router, TypeScript, Tailwind v4, AuthContext   │
                       └───────────────────────────┬────────────────────────────┘
                                                   │
                                      HTTP / JSON  │  httpOnly Cookie
                                      (Bearer JWT) │  (Refresh Token)
                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI Backend (Single Service)                              │
│                                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                 Transport Layer (app/api/v1/)                               │  │
│  │   /auth        /movies       /genres       /ratings       /watchlist       /recommendations │  │
│  └───────────────────────────────────────────────┬─────────────────────────────────────────────┘  │
│                                                  │                                                │
│  ┌───────────────────────────────────────────────▼─────────────────────────────────────────────┐  │
│  │                                  Service Layer (app/services/)                              │  │
│  │   auth_service       movie_service       rating_service       watchlist_service             │  │
│  │   enrichment_service notification_service recommendation_service training_service           │  │
│  └───────────────────────┬───────────────────────────────────────┬─────────────────────────────┘  │
│                          │                                       │                                │
│       SQLAlchemy 2.0     │                       Surprise SVD /  │ SentenceTransformers           │
│       Session / ORM      │                       Pickle Cache    │ Cosine Sim                     │
│                          ▼                                       ▼                                │
│  ┌───────────────────────────────────┐       ┌─────────────────────────────────────────────────┐  │
│  │       Persistence Layer           │       │          ML Subsystem (app/ml/)                 │  │
│  │   app/db/models.py (PostgreSQL)   │       │   svd_baseline_v1.pkl, content_matrix_cache.pkl │  │
│  └───────────────────────────────────┘       └─────────────────────────────────────────────────┘  │
└─────────────────────────────────┬─────────────────────────────────────┬───────────────────────────┘
                                  │                                     │
                                  ▼                                     ▼
                     ┌────────────────────────┐            ┌────────────────────────┐
                     │ PostgreSQL 17 Database │            │   Redis 7 (In-Memory)  │
                     │ (Relational Data &     │            │ (Broker & Result       │
                     │ Foreign Key Cascades)  │            │ Backend for Celery)    │
                     └────────────────────────┘            └────────────┬───────────┘
                                                                        │
                                   ┌────────────────────────────────────┴───────────────────────────┐
                                   ▼                                                                ▼
                     ┌───────────────────────────┐                    ┌───────────────────────────┐
                     │       Celery Worker       │                    │        Celery Beat        │
                     │  - Discovery Task         │                    │  - Daily new release sync │
                     │  - Enrichment Task        │                    │  - Hourly enrichment      │
                     │  - LLM Notification Task  │                    │  - Daily notification run │
                     └─────────────┬─────────────┘                    └───────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   ┌──────────────────────┐                  ┌──────────────────────┐
   │       TMDB API       │                  │       Groq API       │
   │ Metadata & Discovery │                  │ LLM Blurb Generation │
   └──────────────────────┘                  └──────────────────────┘
```

---

## 3. Repository Structure & Code Boundaries

```
movie-app/
├── .github/                       # GitHub configurations and workflows
├── .vscode/
│   └── settings.json              # Python analysis extra paths (pointing to ./apps/api)
├── apps/
│   ├── api/                       # Single-service FastAPI Backend
│   │   ├── alembic.ini            # Alembic database migration config
│   │   ├── pytest.ini             # Pytest test discovery and markers
│   │   ├── requirements.txt       # Python dependencies
│   │   ├── .env.example           # Backend environment template
│   │   ├── app/
│   │   │   ├── main.py            # FastAPI factory, middleware, router mount, health check
│   │   │   ├── api/
│   │   │   │   └── v1/            # HTTP Routers (Thin transport: validate, call service, return)
│   │   │   │       ├── auth.py
│   │   │   │       ├── genres.py
│   │   │   │       ├── movies.py
│   │   │   │       ├── notifications.py
│   │   │   │       ├── ratings.py
│   │   │   │       ├── recommendations.py
│   │   │   │       └── watchlist.py
│   │   │   ├── core/              # Shared infrastructure & cross-cutting concerns
│   │   │   │   ├── celery_app.py  # Celery instance, broker config, beat schedules
│   │   │   │   ├── config.py      # Pydantic BaseSettings (environment variables)
│   │   │   │   ├── dependencies.py# FastAPI dependencies (get_current_user, require_admin)
│   │   │   │   ├── error_handlers.py # Global exception handlers mapping domain errors to HTTP
│   │   │   │   ├── exceptions.py  # Custom exception hierarchy (AppError, NotFoundError, etc.)
│   │   │   │   └── security.py    # bcrypt password hashing, JWT creation/decoding, token hashing
│   │   │   ├── db/
│   │   │   │   ├── database.py    # SQLAlchemy engine, sessionLocal, Base declarative class
│   │   │   │   └── models.py      # All SQLAlchemy ORM models and Enums
│   │   │   ├── ml/                # Machine Learning models and inference utilities
│   │   │   │   ├── model_loader.py# SVD model loader with mtime cache
│   │   │   │   ├── models/        # Serialized models and matrices
│   │   │   │   │   ├── content_matrix_cache.pkl       # Serialized MiniLM embeddings & genre matrix
│   │   │   │   │   ├── svd_baseline_v1.pkl            # Trained Surprise SVD model
│   │   │   │   │   └── svd_baseline_v1_metadata.json  # Training parameters & evaluation metrics
│   │   │   │   └── training/
│   │   │   │       ├── notebooks/ # Jupyter notebooks for data analysis & exploration
│   │   │   │       │   └── 01_exploration.ipynb
│   │   │   │       └── train_cf.py
│   │   │   ├── schemas/           # Pydantic models (API request/response contracts)
│   │   │   │   ├── genre.py
│   │   │   │   ├── movie.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── rating.py
│   │   │   │   ├── recommendation.py
│   │   │   │   ├── user.py
│   │   │   │   └── watchlist.py
│   │   │   ├── services/          # Domain business logic (raises domain exceptions, handles DB)
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── enrichment_service.py
│   │   │   │   ├── genre_service.py
│   │   │   │   ├── movie_service.py
│   │   │   │   ├── notification_service.py
│   │   │   │   ├── rating_service.py
│   │   │   │   ├── recommendation_service.py
│   │   │   │   ├── training_service.py
│   │   │   │   └── watchlist_service.py
│   │   │   └── tasks/             # Celery background tasks
│   │   │       ├── discovery.py   # TMDB /movie/now_playing scraper
│   │   │       ├── enrichment.py  # Asynchronous metadata enricher
│   │   │       └── notifications.py# Candidate matching & LLM notification generator
│   │   ├── migrations/            # Alembic versioned schema migrations
│   │   │   ├── env.py
│   │   │   └── versions/          # Ordered migration scripts
│   │   └── tests/                 # Test suite (Isolated PostgreSQL test DB)
│   │       ├── conftest.py        # Fixtures, test database setup, mock users, clients
│   │       ├── integration/       # HTTP integration tests (FastAPI TestClient)
│   │       │   ├── test_auth_api.py
│   │       │   ├── test_movies_api.py
│   │       │   ├── test_ratings_api.py
│   │       │   └── test_watchlist_api.py
│   │       └── unit/              # Pure unit tests (mocked/isolated service tests)
│   │           ├── test_auth_service.py
│   │           ├── test_movie_service.py
│   │           ├── test_rating_service.py
│   │           └── test_watchlist_service.py
│   └── web/                       # Next.js 16 (React 19) Frontend
│       ├── package.json           # Dependencies: lucide-react, tailwindcss v4
│       ├── tsconfig.json          # TypeScript compiler options (@/* path aliases)
│       ├── next.config.ts         # Remote image domains (TMDB image host)
│       ├── public/                # Static public assets
│       └── src/
│           ├── app/               # Next.js App Router pages
│           │   ├── layout.tsx     # Root layout with AuthProvider & global Navbar
│           │   ├── globals.css    # Tailwind v4 theme & semantic design tokens
│           │   ├── page.tsx       # Root index (redirects to /movies)
│           │   ├── login/page.tsx # User login interface
│           │   ├── signup/page.tsx# User registration interface
│           │   ├── movies/
│           │   │   ├── page.tsx   # Catalog browse (search, genre filter, infinite scroll)
│           │   │   └── [id]/page.tsx # Movie detail view (hero, metadata, rating, watchlist)
│           │   └── watchlist/page.tsx # User watchlist with status filters
│           ├── components/        # Reusable UI component library
│           │   ├── BackButton.tsx
│           │   ├── Button.tsx     # Solid, outline, ghost variants with focus rings
│           │   ├── Logo.tsx
│           │   ├── MovieCard.tsx
│           │   ├── Navbar.tsx     # Responsive navigation with authenticated state
│           │   ├── RatingWidget.tsx # Interactive 10-point half-star widget
│           │   └── WatchlistButton.tsx # Three-state dropdown/toggle button
│           ├── context/
│           │   └── AuthContext.tsx# In-memory JWT access token & silent session restore
│           ├── hooks/
│           │   └── useGuestOnly.ts# Route protection redirecting logged-in users away from auth
│           ├── lib/
│           │   ├── api-client.ts  # Typed fetch wrapper with credentials: "include"
│           │   ├── api-error.ts   # Client-side API error parsing
│           │   └── api/           # Domain API client methods
│           │       ├── auth.py -> auth.ts
│           │       ├── genre.ts
│           │       ├── movies.ts
│           │       ├── ratings.ts
│           │       └── watchlist.ts
│           └── types/             # Frontend TypeScript interfaces & enums
│               ├── genre.ts
│               ├── movie.ts
│               ├── ratings.ts
│               ├── user.ts
│               └── watchlist.ts
├── data/
│   └── ml-20m/                    # MovieLens 20M Dataset (Raw CSVs)
│       ├── genome-scores.csv
│       ├── genome-tags.csv
│       ├── links.csv              # Mapping: movieId <-> imdbId <-> tmdbId
│       ├── movies.csv             # 27,278 movie titles & pipe-delimited genres
│       ├── ratings.csv            # 20,000,263 ratings on 0.5-5.0 scale
│       └── tags.csv
├── docs/
│   ├── progress.md                # Historical log of development iterations
│   └── decisions/                 # Formal Architecture Decision Records (ADRs)
│       ├── 001-movie-id-strategy.md
│       ├── 002-single-fastapi-service.md
│       └── 003-seed-user-reconsideration.md
├── infra/
│   └── docker-compose.yml         # Containerized PostgreSQL 17 & Redis 7
├── scripts/
│   └── seed/
│       ├── seed_movielens.py      # Parses ml-20m, resolves tmdb_id, seeds PostgreSQL
│       └── enrich_tmdb.py         # Standalone batch enrichment CLI runner
├── movie-recommender-project-plan.md # Original multi-milestone roadmap
└── README.md
```

---

## 4. Architecture Decision Records (ADRs)

### ADR 001: `tmdb_id` as the Canonical Movie Identifier
- **Context:** The application bridges two data sources: historical MovieLens (`ml-20m`) and live TMDB metadata. The internal database requires a durable primary identifier.
- **Decision:** `tmdb_id` (String) is the canonical, unique external identifier for every movie. `movielens_id` (Integer) is stored as an optional unique column, utilized exclusively during offline recommender model training to join historical ratings.
- **Rationale:** TMDB is the live ongoing data source for posters, trailers, casting, and new releases. Any movie released after MovieLens was frozen has a TMDB ID but no MovieLens ID. Movies in `links.csv` without a valid TMDB link are discarded during seeding to ensure the invariant that every valid catalog item has a canonical `tmdb_id`.

### ADR 002: Single FastAPI Service Architecture
- **Context:** Deciding between a distributed microservices pattern (Express Node.js product API + FastAPI ML serving) versus a unified backend.
- **Decision:** Build a single FastAPI service housing both product REST routes and ML serving, while maintaining an explicit internal module boundary (`app/api/` vs `app/services/` vs `app/ml/`).
- **Rationale:** Deepening expertise in Python's async and ML ecosystem provides higher compounding engineering value than context-switching across two language runtimes. Eliminates network serialization overhead between API and recommendation models. The clean internal boundary ensures the ML serving module can be factored into a dedicated microservice in the future without modifying domain business logic.

### ADR 003: Seed User Invariant & Structural Security
- **Context:** MovieLens historical ratings (~138,000 users) are needed to train and bootstrap collaborative filtering. Foreign key integrity requires user records to exist in the database.
- **Decision:** Introduce a boolean `is_seed_user = True` flag on the `users` table. Seed users are populated with deterministic, honest synthetic identities (e.g. `movielens_user_1@seed.local`).
- **Safety Mechanism:** Seed users **never possess a row in `user_credentials`**. Authentication strictly mandates querying `user_credentials` before verifying passwords. Because no credentials row exists, authentication for seed users is structurally impossible at the database level, without weakening `NOT NULL` constraints on `users.email` or `users.username`.

---

## 5. Data Backbone & Data Pipeline

### 5.1 The MovieLens 20M Dataset (`ml-20m`)
The offline recommendation system is founded on the MovieLens 20M dataset:
- **Total records:** 20,000,263 ratings across 27,278 movies created by 138,493 users between 1995 and 2015.
- **Scale:** 0.5 to 5.0 stars with 0.5 increments. Matches our live application rating scale directly, eliminating normalization discrepancies between historical and live ratings.
- **Sparsity Analysis:** 99.46% matrix sparsity.
- **Pruning Cutoff:** Filtered to movies with **$\ge 5$ ratings**.
  - Catalog impact: 18,345 movies retained (68.6% of raw catalog).
  - Rating impact: 19,984,024 ratings retained (**99.92% of all ratings preserved**).
  - Trims long-tail catalog noise while preserving statistical density. Unfiltered movies remain browsable and are served by content-based filtering.

### 5.2 Seeding Pipeline (`scripts/seed/seed_movielens.py`)
1. Reads `links.csv` into memory to build the `movieId -> tmdbId` hash map.
2. Streams `movies.csv`, parses titles and release years via regular expressions (`r"^(.*)\s\((\d{4})\)\s*$"`), and extracts genre tokens.
3. Slugs and creates unique `Genre` records with in-memory caching.
4. Batch-inserts movies with initial status `MovieStatus.released`, `adult=False`, and `poster_path=None` (indicating pending enrichment). Commits in batches of 500 rows.

### 5.3 TMDB Metadata Enrichment Pipeline (`enrichment_service.py`)
Because MovieLens only provides titles and genre tags, comprehensive movie details are enriched asynchronously via TMDB:
- **Rate-Limiting & Backoff:** 0.5s pause between requests. Handles HTTP 429 by extracting `Retry-After` header. Automatic retry on socket timeouts up to 3 attempts.
- **Fail-Fast Auth Handling:** HTTP 401 raises `TMDBAuthError` immediately. This prevents a bad API key from treating existing movies as 404s.
- **The Poster Path Sentinel:**
  - `poster_path IS NULL`: Movie has not yet been processed by the enrichment job.
  - `poster_path = ""` (empty string): Movie was queried on TMDB and returned HTTP 404 (confirmed unmatched).
  - `poster_path = "/path.jpg"`: Movie successfully enriched.
  - *Public API Filter:* The helper `_enriched_only(query)` enforces `Movie.poster_path.isnot(None)` and `Movie.poster_path != ""` so unmatched or unenriched movies never appear on public browsing rails.

---

## 6. Database Schema & Persistence Layer

The database uses PostgreSQL 17 with SQLAlchemy 2.0 ORM and Alembic migrations.

```
┌──────────────────┐       ┌──────────────────────┐       ┌───────────────────┐
│      users       │       │   user_credentials   │       │   refresh_tokens  │
├──────────────────┤       ├──────────────────────┤       ├───────────────────┤
│ id (PK)          │◄──────│ id (PK)              │       │ id (PK)           │
│ email (UQ, NN)   │ 1   1 │ user_id (FK, UQ, NN) │   ┌───┤ user_id (FK, NN)  │
│ username (UQ, NN)│       │ password_hash (NN)   │   │   │ token_hash (UQ,NN)│
│ name             │       │ created_at           │   │   │ expires_at (NN)   │
│ role (Enum, NN)  │       │ updated_at           │   │   │ revoked_at        │
│ is_seed_user (NN)│       └──────────────────────┘   │   │ created_at (NN)   │
│ created_at (NN)  │                                  │   └───────────────────┘
│ updated_at (NN)  │                                  │
└────────┬─────────┘                                  │
         │ 1                                          │
         │         ┌──────────────────────────────────┘
         │         │
         │ N       ▼ N
┌────────┴──────────────┐       ┌───────────────────────┐       ┌───────────────────┐
│        ratings        │       │    watchlist_items    │       │   notifications   │
├───────────────────────┤       ├───────────────────────┤       ├───────────────────┤
│ id (PK)               │       │ id (PK)               │       │ id (PK)           │
│ user_id (FK, CASCADE) │       │ user_id (FK, CASCADE) │       │ user_id (FK, CASC)│
│ movie_id (FK, CASCADE)│       │ movie_id (FK, CASCADE)│       │ movie_id(FK, CASC)│
│ rating (Float, NN)    │       │ status (Enum, NN)     │       │ message (Text, NN)│
│ rated_at (NN)         │       │ added_at (NN)         │       │ is_read (Bool, NN)│
│ updated_at (NN)       │       │ watched_at            │       │ created_at (NN)   │
├───────────────────────┤       ├───────────────────────┤       ├───────────────────┤
│ UQ(user_id, movie_id) │       │ UQ(user_id, movie_id) │       │ UQ(user, movie)   │
└───────────┬───────────┘       └───────────┬───────────┘       └─────────┬─────────┘
            │ N                             │ N                           │ N
            └───────────────────────┐       │                             │
                                    ▼       ▼                             ▼
                            ┌───────────────────────────────────────────────────────┐
                            │                        movies                         │
                            ├───────────────────────────────────────────────────────┤
                            │ id (PK)                                               │
                            │ tmdb_id (UQ, NN)                                      │
                            │ imdb_id (UQ, Nullable)                                │
                            │ movielens_id (UQ, Nullable)                           │
                            │ title (NN)                                            │
                            │ original_title                                        │
                            │ tagline                                               │
                            │ description (Text)                                    │
                            │ runtime                                               │
                            │ released_on (Date)                                    │
                            │ poster_path (Sentinel: NULL / "" / path)              │
                            │ backdrop_path                                         │
                            │ original_language                                     │
                            │ status (MovieStatus Enum, NN)                         │
                            │ budget, revenue                                       │
                            │ adult (Bool, NN)                                      │
                            │ tmdb_vote_average, tmdb_vote_count                    │
                            │ trailer_link                                          │
                            │ notified_at (DateTime)                                │
                            │ created_at (NN), updated_at (NN)                      │
                            └───────────────┬───────────────────────────────────────┘
                                            │ N
                                            │
                                            ▼ M
                            ┌───────────────────────────────────┐
                            │           movie_genres            │
                            ├───────────────────────────────────┤
                            │ movie_id (PK, FK movies.id)       │
                            │ genre_id (PK, FK genres.id)       │
                            └─────────────────┬─────────────────┘
                                              │ M
                                              │
                                              ▼ 1
                            ┌───────────────────────────────────┐
                            │              genres               │
                            ├───────────────────────────────────┤
                            │ id (PK)                           │
                            │ name (UQ, NN)                     │
                            │ slug (UQ, NN)                     │
                            │ created_at (NN)                   │
                            └───────────────────────────────────┘
```

### 6.1 Database Models Summary (`app/db/models.py`)
- **`User`**: Identity model. `role` enum (`user`, `admin`). `is_seed_user` boolean. Has one `UserCredentials`, many `Rating`, many `WatchlistItem`.
- **`UserCredentials`**: Strict separation of credential security from profile identity. Stores bcrypt `password_hash`.
- **`RefreshToken`**: Opaque token hash (`token_hash` via SHA-256), `expires_at`, and `revoked_at` (nullable; set on rotation or logout).
- **`Movie`**: Core movie entity. Canonical identity is `tmdb_id`. Enriched attributes include revenue, runtime, release date, TMDB vote statistics, and the `notified_at` marker for AI notification deduplication.
- **`Genre`**: Lookup table (`name`, `slug`). Connected to `Movie` via `movie_genres` secondary table.
- **`Rating`**: Stores user movie ratings (0.5 to 5.0). Enforces `UniqueConstraint("user_id", "movie_id")` and `ondelete="CASCADE"`.
- **`WatchlistItem`**: Tracks user saved movies. `status` is a `WatchlistStatus` enum (`want_to_watch`, `watched`, `abandoned`). Maintains set-once timestamp semantics for `watched_at`.
- **`Notification`**: Broadcasts release alerts to users. Linked via foreign keys to `User` and `Movie`.
- **`Person`, `MovieCast`, `Platform`, `MoviePlatform`**: Schemas and database models exist for future expansion of cast, crew, and streaming availability.

---

## 7. Authentication, Authorization & Security

### 7.1 Token Model & Lifecycle
- **Access Tokens:**
  - Standard JSON Web Token (JWT) signed with `HS256`.
  - Expiration: Short-lived (30 minutes).
  - Claims: `sub` (User ID string), `exp` (UTC expiration timestamp), `jti` (unique 16-character cryptographic nonce to prevent replay attacks).
  - Storage: In-memory only in frontend state (`AuthContext.tsx`). Never placed in `localStorage` or `sessionStorage`.
- **Refresh Tokens:**
  - 64-byte high-entropy URL-safe cryptographic token (`secrets.token_urlsafe(64)`).
  - Stored server-side exclusively as a **SHA-256 hash** (`hashlib.sha256`).
  - Transport: Stored in an **`httpOnly` cookie** named `refresh_token`, with `SameSite=Lax`, `Secure` (in production), path restricted strictly to `/api/v1/auth`, and 30-day lifetime.
  - **Atomic Token Rotation:** On every call to `/api/v1/auth/refresh`, the presented token is validated and revoked (`revoked_at = utcnow()`), and an entirely new refresh token is issued within the **same database transaction**.
  - **Revocation & Reuse Detection:** Attempting to reuse a revoked token fails immediately (`401 Unauthorized`).

### 7.2 Role-Based Access Control (RBAC)
- Defined by `UserRole` enum (`user`, `admin`).
- Admin promotion is performed via direct database administrative intervention (no self-serve or publicly exposed promotion endpoint).
- FastAPI dependency `require_admin` inspects `current_user.role == UserRole.admin` and guards administrative mutations:
  - `POST /api/v1/movies`
  - `POST /api/v1/genres`

### 7.3 Centralized Error Handling Model
Routes and services never instantiate `HTTPException` directly. The application uses a custom domain exception hierarchy mapped via global handlers in `app/core/error_handlers.py`:

```
AppError (base exception)
├── NotFoundError       -> HTTP 404 Not Found
├── UnauthorizedError   -> HTTP 401 Unauthorized
├── ForbiddenError      -> HTTP 403 Forbidden
├── BusinessRuleError   -> HTTP 400 Bad Request
└── ConflictError       -> HTTP 409 Conflict
```
- **IntegrityError:** Mapped automatically to HTTP 409 Conflict with a sanitized error message (`"A record with this value already exists."`).
- **RequestValidationError:** Mapped to HTTP 422 Unprocessable Content.
- **Service Mutation Rollbacks:** Service layer functions wrap mutating database operations in `try / except` blocks, triggering `db.rollback()` before re-raising domain exceptions.

---

## 8. Recommendation Engine & ML Architecture

The application provides three recommendation surfaces and an algorithmic cold-start fallback.

```
                                  RECOMMENDATION REQUEST
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             Known User Profile?                           Anonymous / Cold Start?
                       │                                           │
         ┌─────────────┴─────────────┐                             ▼
         ▼                           ▼                   IMDb Weighted Rating
  Collaborative Filtering     Content-Based               Formula (Popularity)
    (Surprise SVD Model)      (SentenceTransformer         (Catalog 60th Percentile)
         │                     + Genre Matrix)                     │
         │                           │                             │
         └─────────────┬─────────────┘                             │
                       ▼                                           │
                 Hybrid Blending                                   │
              ("For You" Surface)                                  │
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             ▼
                                  Ranked Movie List
```

### 8.1 Surface 1: "Users with Similar Taste" (Collaborative Filtering)
- **Algorithm:** Singular Value Decomposition (SVD) matrix factorization via `scikit-surprise`.
- **Training Hyperparameters:** `n_factors = 50`, `n_epochs = 20`, `random_state = 42`.
- **Filter Precondition:** Movies with $\ge 5$ ratings in `ml-20m`.
- **Evaluation & Metrics:**
  - Model Artifact: `svd_baseline_v1.pkl`
  - Prediction Accuracy: **RMSE = 0.786** (evaluated on held-out test split).
  - Ranking Performance: **Hit Rate@10 = 0.4757** (47.57%).
  - **Evaluation Methodology:** Sampled-negative evaluation. For 3,000 sampled users, 1 known held-out positive rating ($\ge 4.0$) is blended with 99 randomly sampled unrated items (negatives). Hit Rate@10 measures the percentage of test users where the true positive was successfully ranked into the top 10 positions.
- **Inference Pipeline (`recommendation_service.py`):**
  - Model loader uses an mtime file-stat check to cache the deserialized pickle model in memory, reloading automatically if retrained.
  - Translates `movielens_user_id` to inner UID; extracts already-rated items from the user rating list (`trainset.ur[inner_uid]`).
  - Predicts expected rating across all unrated candidate movies, sorts descending, maps to `tmdb_id`, and pulls enriched database entities.

### 8.2 Surface 2: "Because You Liked X" (Content-Based Filtering)
- **Vector Semantic Representation:** Uses the `all-MiniLM-L6-v2` SentenceTransformer model to compute 384-dimensional dense semantic embeddings for movie overviews (`Movie.description`). Embeddings are L2-normalized:
  $$\hat{e} = \frac{e}{\|e\|_2}$$
- **Genre Categorical Representation:** One-hot encoded matrix across all catalog genres, L2-normalized:
  $$\hat{g} = \frac{g}{\|g\|_2}$$
- **Caching Mechanism:** Precomputed embeddings and genre matrices are serialized to `apps/api/app/ml/models/content_matrix_cache.pkl` and cached in process memory using `@lru_cache(maxsize=1)`.
- **Combined Similarity Metric:** For an input movie $A$ and candidate movie $B$:
  $$\text{Score}(A, B) = 0.6 \cdot (\hat{e}_A \cdot \hat{e}_B) + 0.4 \cdot (\hat{g}_A \cdot \hat{g}_B)$$
- Candidates are ranked by combined cosine similarity, excluding the query movie.

### 8.3 Surface 3: "For You" (Hybrid Engine)
- Combines collaborative filtering with content-based preference.
- Pipeline:
  1. Requests a large candidate pool ($3 \times N$) from the collaborative filtering SVD model.
  2. Identifies the user's highest-rated historical movie as the content "anchor".
  3. Computes content similarity between the anchor movie and all SVD candidates using the precomputed content matrix.
  4. Blends scores using configurable weighting ($\alpha = 0.5$):
     $$\text{HybridScore} = \alpha \cdot \left(1.0 - \frac{\text{Rank}_{\text{CF}}}{|\text{Candidates}|}\right) + (1.0 - \alpha) \cdot \text{Score}_{\text{Content}}(\text{Anchor}, \text{Movie})$$
  5. Returns the top $N$ ranked movies.

### 8.4 Baseline Fallback: "Popular / Trending" (IMDb Weighted Rating)
For cold-start or anonymous sessions, the application falls back to IMDb's Bayesian weighted formula:
$$WR = \left(\frac{v}{v + m}\right) \cdot R + \left(\frac{m}{v + m}\right) \cdot C$$
Where:
- $v$: Movie's TMDB vote count (`Movie.tmdb_vote_count`).
- $R$: Movie's TMDB average vote (`Movie.tmdb_vote_average`).
- $C$: Mean average vote across the entire enriched catalog ($\approx 6.0$).
- $m$: Minimum vote threshold, dynamically calculated as the **60th percentile** of vote counts across the active database catalog.

---

## 9. Background Processing & AI Notification Pipeline

The background worker architecture is built with Celery and Redis.

```
       CELERY BEAT SCHEDULER
                 │
  ┌──────────────┼───────────────────────────┐
  │ (Every 24h)  │ (Every 1h)                │ (Every 24h)
  ▼              ▼                           ▼
sync_new_releases enrich_pending_movies   generate_notifications
  │              │                           │
  │ Queries TMDB │ Calls TMDB Details API    │ 1. Find releases in last 30 days
  │ /now_playing │ Applies runtime, budget,  │ 2. Match users with ratings >= 4.0
  │ Inserts rows │ posters, backdrop.        │ 3. Score content similarity >= 0.55
  │ with NULL    │ Marks 404s with ""        │ 4. Groq LLM generates copy
  │ poster_path  │                           │ 5. Inserts Notification records
```

### 9.1 Periodic Task Schedule (`app/core/celery_app.py`)
| Task Identifier | Scheduled Interval | Module & Function | Purpose |
|---|---|---|---|
| `sync-new-releases-daily` | Every 24 hours | `app.tasks.discovery.sync_new_releases` | Queries TMDB `/movie/now_playing`, ingests fresh theatrical releases. |
| `enrich-new-movies-hourly` | Every 1 hour | `app.tasks.enrichment.enrich_pending_movies_task` | Processes unenriched rows (`poster_path IS NULL`). |
| `generate-notifications-daily` | Every 24 hours | `app.tasks.notifications.generate_notifications` | Matches new releases to users and writes personalized notifications. |

### 9.2 The AI Notification Generation Pipeline
1. **Target Selection (`get_pending_movies`):** Queries movies where `poster_path` is valid, `status == MovieStatus.released`, `released_on` is within the last 30 days, and `notified_at IS NULL`.
2. **Audience Matching (`find_interested_users`):**
   - Retrieves all user ratings where `rating >= 4.0`.
   - Compares the candidate release against each user's top-rated movies using the semantic + genre embedding matrix ($0.6 \times \text{semantic} + 0.4 \times \text{genre}$).
   - If the maximum similarity score meets or exceeds the **relevance threshold ($\ge 0.55$)**, the user is flagged as interested, with the closest match recorded as the "anchor movie".
3. **LLM Synthesis (`generate_notification_text`):**
   - Uses the Groq API (via the `OpenAI` client SDK) with the `openai/gpt-oss-20b` model.
   - Prompt constraint: Under 20 words, personalized to the user's affinity for the anchor movie, without promotional clichés, hashtags, or emojis.
   - Example prompt: *"Write one short, friendly sentence (under 20 words) telling a movie fan that a new movie called '{new_movie}' just released, and that it's a good match because they loved '{liked_movie}'. No hashtags, no emojis, no exclamation marks. Just the sentence."*
4. **Delivery & Deduplication:**
   - Checks `notification_exists(db, user_id, movie.id)`.
   - Inserts row into `notifications`.
   - Updates `movie.notified_at = utcnow()` to prevent duplicate notifications across scheduler cycles.

---

## 10. Backend REST API Specification

All API routes are prefixed under `/api/v1`.

### 10.1 Authentication (`/auth`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | No | Creates new `User` and `UserCredentials`. Status 201. |
| `POST` | `/auth/login` | No | Returns `{ access_token }` and sets `refresh_token` httpOnly cookie. |
| `POST` | `/auth/refresh` | Cookie | Rotates refresh token in cookie and returns new `{ access_token }`. |
| `POST` | `/auth/logout` | Optional | Revokes refresh token in database, clears cookie. Status 204. |
| `GET` | `/auth/me` | Bearer JWT | Returns current authenticated `UserResponse`. |

### 10.2 Movies (`/movies`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/movies/` | No | Catalog list. Query params: `skip` (int), `limit` (1-100), `q` (title search, contains-match), `genre_id` (filter). |
| `GET` | `/movies/{movie_id}` | No | Full detail for movie with genres, vote stats, backdrop. |
| `POST` | `/movies/` | Admin JWT | Admin endpoint to create movie. Body: `MovieCreate`. Status 201. |

### 10.3 Genres (`/genres`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/genres/` | No | Lists all movie genres. |
| `POST` | `/genres/` | Admin JWT | Admin endpoint to create genre. Body: `GenreCreate`. Status 201. |

### 10.4 Ratings (`/ratings`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/ratings/` | Bearer JWT | Upserts rating for movie (`0.5 <= rating <= 5.0`). Status 201. |
| `GET` | `/ratings/me` | Bearer JWT | Returns all ratings submitted by current user. |
| `GET` | `/ratings/movie/{movie_id}` | Bearer JWT | Returns current user's rating for specific movie. |
| `DELETE` | `/ratings/movie/{movie_id}` | Bearer JWT | Deletes rating for movie. Status 204. |

### 10.5 Watchlist (`/watchlist`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/watchlist/` | Bearer JWT | Adds movie to watchlist (default `want_to_watch`). Status 201. |
| `GET` | `/watchlist/me` | Bearer JWT | Returns user watchlist. Query param: `status` filter. |
| `GET` | `/watchlist/movie/{movie_id}` | Bearer JWT | Checks if movie is in user watchlist. |
| `PATCH` | `/watchlist/movie/{movie_id}` | Bearer JWT | Updates status (`want_to_watch`, `watched`, `abandoned`). Sets `watched_at` on first transition to `watched`. |
| `DELETE` | `/watchlist/movie/{movie_id}` | Bearer JWT | Removes movie from watchlist. Status 204. |

### 10.6 Recommendations (`/recommendations`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/recommendations/similar-taste/{movielens_user_id}` | No | Top-N collaborative filtering predictions via SVD. |
| `GET` | `/recommendations/because-you-liked/{movie_id}` | No | Top-N content-based recommendations (SentenceTransformer + genres). |
| `GET` | `/recommendations/for-you/{movielens_user_id}` | No | Top-N hybrid recommendations (SVD + content anchor similarity). |
| `GET` | `/recommendations/popular` | No | Cold-start baseline using IMDb weighted rating formula. |

### 10.7 Notifications (`/notifications`)
| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/notifications/me` | Bearer JWT | Returns user notifications. Query param: `unread_only` (bool). |
| `PATCH` | `/notifications/{notification_id}/read` | Bearer JWT | Marks specific notification as read (`is_read = True`). |

---

## 11. Frontend Architecture & Design System

### 11.1 Technology Stack
- **Framework:** Next.js 16 (App Router) with React 19.
- **Language:** TypeScript 5.
- **Styling:** Tailwind CSS v4 using CSS variables and semantic design tokens.
- **Icons:** `lucide-react`.

### 11.2 Design Tokens & Visual Hierarchy (`globals.css`)
- **Palette:** Near-white / near-black high-contrast modern cinematic aesthetic.
  - Background: Pure black `#000000` with subtle elevated card layers `#121212`, `#1A1A1A`.
  - Foreground: Near-white `#EDEDED` and muted neutral typography `#A1A1A1`.
  - Accent: Vibrant cinema coral-red (`#E54D2E`, hover `#F76808`).
- **Typography:**
  - Headlines & Hero Displays: `Instrument Serif` (editorial, cinematic elegance).
  - Body & UI Interfaces: `Geist Sans` (clean legibility).
  - Numeric & Metadata: `Geist Mono` (runtimes, ratings, dates).
- **Component Primitives:**
  - `Button`: Encapsulates `solid`, `outline`, and `ghost` variants with keyboard focus ring accessibility.
  - `MovieCard`: Poster display with aspect ratio locking, fallback image handling, and hover lift effects.
  - `RatingWidget`: 10-point half-star interactive widget supporting optimistic state, keyboard navigation, and logged-out prompts.
  - `WatchlistButton`: Three-state drop-down/toggle with optimistic UI updates and error rollback.

### 11.3 State Management & Data Fetching Patterns
- **`AuthContext.tsx`:** Manages authentication state in memory. On application mount, invokes `tryRestoreSession()` (`POST /api/v1/auth/refresh`), restoring access tokens transparently from the httpOnly refresh cookie without requiring page redirects.
- **Typed API Client (`lib/api-client.ts`):** Centralized `apifetch<T>` wrapper handling HTTP headers, authorization bearer tokens, credentials forwarding (`credentials: "include"`), and structured error translation (`ApiError`).
- **Generational Infinite Scroll (`/movies/page.tsx`):** Implements an incrementing generation counter (`generationRef`) to prevent stale pagination responses from overwriting newer query results when users type rapidly into the search filter.

---

## 12. Testing Architecture & Quality Assurance

### 12.1 Database Isolation Strategy (`apps/api/tests/conftest.py`)
- Tests run against a dedicated PostgreSQL database (`movie_db_test`), not an in-memory SQLite database.
- **Rationale:** SQLite does not natively support PostgreSQL `Enum` types or declarative `ondelete="CASCADE"` foreign key constraints. Testing against real PostgreSQL guarantees schema behavior parity with production.
- **Transaction Rollback Pattern:** Each test runs inside a nested database transaction using SAVEPOINTs. Commits executed inside service methods do not persist across tests, ensuring total test isolation without re-running migrations.

### 12.2 Integration Test Suites
- `test_auth_api.py`: Validates user registration, password hashing, login token generation, refresh token cookie persistence, token rotation, and reuse rejection.
- `test_movies_api.py`: Tests search filtering (verifying contains-match), genre query restrictions, admin-only creation gates, and unenriched poster exclusions.
- `test_ratings_api.py`: Validates half-star bounds, rating upsert behavior on re-rating, and cross-user data isolation.
- `test_watchlist_api.py`: Verifies item addition, removal, status updates, and the invariant that `watched_at` is stamped only on the first transition to `watched`.

### 12.3 Unit Test Suites
Unit tests isolate `auth_service`, `movie_service`, `rating_service`, and `watchlist_service` with direct mock sessions, testing business logic exceptions, boundary validations, and rollback behavior.

---

## 13. Engineering Wins & Case Studies (Bugs Found & Fixed)

1. **The Pydantic `exclude` Bug:**
   - *Problem:* In `movie_service.create_movie`, `payload.model_dump(exclude="genre_ids")` passed a raw string instead of a set (`exclude={"genre_ids"}`). Pydantic interpreted the string as a sequence of character keys (`'g', 'e', 'n', 'r', ...`), leaving `genre_ids` in the dictionary and causing `Movie(**data)` to crash on an unexpected keyword argument.
   - *Fix:* Corrected to `exclude={"genre_ids"}` and verified with a unit test (`test_create_movie_with_genres_succeeds`).

2. **Movie Search Regression (Prefix vs. Contains):**
   - *Problem:* Movie search silently regressed from a contains search (`%q%`) to a prefix search (`q%`), breaking discovery for multi-word queries.
   - *Fix:* Restored `Movie.title.ilike(f"%{q}%")` and locked in behavior with integration tests.

3. **TMDB 401 Fatal Fail-Fast:**
   - *Problem:* During initial data enrichment, HTTP 401 (invalid/expired credentials) was treated as a transient error. The script proceeded, marking hundreds of valid movies with the empty string sentinel (`poster_path = ""`), permanently flagging them as non-existent.
   - *Fix:* Introduced `TMDBAuthError`, terminating the batch run immediately on HTTP 401.

4. **Watchlist vs. Rating Not-Found Consistency:**
   - *Problem:* `watchlist_service.get_watchlist_item_for_movie` returned `None` on a lookup miss, while `rating_service.get_user_rating_for_movie` raised `NotFoundError`.
   - *Fix:* Unified service behavior to raise `NotFoundError` consistently across all entity queries.

5. **Recommender Hit Rate Evaluation Realism:**
   - *Problem:* Initial collaborative filtering evaluation calculated metrics only against a held-out test split of existing ratings. This yielded misleadingly high scores because it evaluated rating reconstruction rather than real-world item ranking across a large catalog.
   - *Fix:* Implemented sampled-negative evaluation (1 true positive hidden amongst 99 sampled unrated negatives per user), yielding an authentic, reproducible Hit Rate@10 of 47.57%.

---

## 14. Milestone Progress & Roadmap

| Milestone | Scope | Status | Notes |
|---|---|:---:|---|
| **0 — Foundations** | Repo layout, MovieLens download, PostgreSQL schema, Docker Compose. | ✅ Done | Initial base established. |
| **1 — Data Pipeline** | MovieLens seeder (`seed_movielens.py`), TMDB enricher (`enrich_tmdb.py`). | 🔄 In Progress | Catalog seeded & enriched. User bulk seed scripts pending. |
| **2 — Backend MVP** | Auth, movies, genres, ratings, watchlist CRUD, custom error hierarchy. | ✅ Done | Fully covered by unit & integration tests. |
| **3 — Frontend MVP** | Catalog browse, infinite scroll, movie detail, watchlist, auth UI. | ✅ Done | Modern theme with semantic tokens and React 19 App Router. |
| **4 — Rec Engine v1** | SVD model training, Hit Rate@10 evaluation, SVD route serving. | ✅ Done | RMSE 0.786, Hit Rate@10 0.4757. Served at `/similar-taste`. |
| **5 — Rec Engine v2** | Content-based filtering, hybrid engine, popular cold-start route. | ✅ Done | SentenceTransformer embeddings + genre cosine blending. |
| **6 — AI Automation** | Celery Beat tasks, new release sync, Groq LLM notification copy. | ✅ Done | Celery tasks running with Redis broker. |
| **7 — Test Hardening** | Full coverage audit, external API mocking, load testing. | 🔄 Partial | Core coverage complete; load testing remaining. |
| **7.5 — Security Review** | Brute force protection on `/auth/login`, CORS review, dependency audit. | ⏳ Planned | Scheduled before containerization. |
| **8 — Containerization** | Dockerfiles for API and Web, GitHub Actions CI (lint, test, build). | ⏳ Planned | Docker Compose exists for Postgres & Redis. |
| **9 — Kubernetes** | Local K8s deployment manifests, Helm charts, Prometheus/Grafana. | ⏳ Planned | Architecture designed for horizontal scaling. |
| **10 — Polish & Packaging**| Final documentation, demo video, architectural whitepaper. | ⏳ Planned | Documentation and context consolidation. |

---

## 15. Environment Configuration & Operational Runbook

### 15.1 Environment Variables

#### Backend (`apps/api/.env`)
```ini
# Application
APP_ENV=development
APP_TITLE="Movie app"
APP_VERSION="0.1.0"
SECRET_KEY=generate-a-strong-random-secret-key

# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/movie_db
TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/movie_db_test

# JWT & Authentication
JWT_SECRET_KEY=generate-a-strong-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis & Celery
REDIS_URL=redis://localhost:6379/0

# TMDB API
TMDB_READ_ACCESS_TOKEN=your-tmdb-v4-bearer-token
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/original

# LLM Generation
GROQ_API_KEY=your-groq-api-key

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

#### Frontend (`apps/web/.env.local`)
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

### 15.2 Operational Runbook

#### 1. Start Infrastructure (PostgreSQL & Redis)
```powershell
# From repository root
docker compose -f infra/docker-compose.yml up -d
```

#### 2. Initialize Backend & Apply Migrations
```powershell
cd apps/api
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

#### 3. Seed Movie Catalog & Enrich Metadata
```powershell
# Seed base MovieLens movies and genres
python ../../scripts/seed/seed_movielens.py

# Run batch metadata enrichment (TMDB API)
python ../../scripts/seed/enrich_tmdb.py
```

#### 4. Run Test Suite
```powershell
# Inside apps/api with virtualenv active
pytest -v
```

#### 5. Start Backend API Server
```powershell
# Inside apps/api with virtualenv active
uvicorn app.main:app --reload --port 8000
```

#### 6. Start Celery Worker & Beat Scheduler
```powershell
# Terminal 1: Celery Worker
cd apps/api
.\venv\Scripts\Activate.ps1
celery -A app.core.celery_app.celery_app worker --loglevel=info -P solo

# Terminal 2: Celery Beat Scheduler
cd apps/api
.\venv\Scripts\Activate.ps1
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

#### 7. Start Frontend Development Server
```powershell
cd apps/web
npm install
npm run dev
# Application will be accessible at http://localhost:3000
```


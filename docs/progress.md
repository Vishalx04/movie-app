# Movie App — Living Progress Doc

Last updated: ~Day 30+, mid-Milestone 4

**Reconciliation note:** this project was worked on across two chat threads in the same project. This doc is the single source of truth going forward — supersedes any earlier, partial progress docs. Update it as the project moves; don't let it go stale again.

---

## 1. Stack

- **Backend:** FastAPI (single service — API + ML in one codebase, `app/api/` vs `app/ml/` internal boundary)
- **DB:** PostgreSQL, SQLAlchemy ORM, Alembic migrations
- **Auth:** JWT access tokens (in-memory client-side) + refresh tokens (httpOnly cookie, hash-stored, rotated on use)
- **Frontend:** Next.js (App Router), TypeScript, Tailwind v4
- **ML:** `scikit-surprise` (SVD collaborative filtering), pandas
- **Data:** MovieLens `ml-20m` (movies + genres seeded and TMDB-enriched, real data live in DB); ratings.csv used for offline model training

---

## 2. Architecture Decisions

### 2.1 Single FastAPI backend
API + ML in one service. Internal boundary preserves the option to split later without a rewrite.

### 2.2 `tmdb_id` as canonical movie ID
`movielens_id` kept only for joining historical ratings offline. **ADR:** `docs/decisions/001-movie-id-strategy.md`

### 2.3 SQLAlchemy + Alembic, two schema layers
SQLAlchemy models = DB shape. Pydantic schemas = API contracts. Never conflated.

### 2.4 Derived fields computed, never stored
`known_for`, `avg_rating`, `recommendations` — computed at request time.

### 2.5 Ratings scale: 0.5–5.0
Matches MovieLens scale so historical + live ratings blend without conversion. Also matches the `Reader(rating_scale=(0.5, 5.0))` config in the CF training pipeline.

### 2.6 Auth: email/password now, OAuth deferred
- `users` — identity only, `email`/`username` `NOT NULL`
- `user_credentials` — separate, optional one-to-one. Seed users have no row here — this is what makes their login structurally impossible, not field nullability.
- `oauth_accounts` — deferred, no frontend flow yet
- `refresh_tokens` — SHA-256 hash-stored, revocable, atomically rotated (single commit for revoke + create)
- Access tokens: short-lived JWT, in-memory only on client
- Refresh tokens: httpOnly cookie, scoped to `/api/v1/auth`

### 2.7 Seed users for MovieLens bootstrap data
`is_seed_user = true`, deterministic honest-placeholder identity, `NOT NULL` constraints satisfied honestly. Cannot log in because no `user_credentials` row exists — not because of nullable fields. **ADR:** `docs/decisions/003-seed-user-reconsideration.md` (documents the full reversal story — rejected, then reinstated via a different mechanism).
**Status: schema ready. Bulk seed scripts (138K users + ratings subset) still not built** — see §7.

### 2.8 Service layer pattern
Routes: parse → call service → return. Business logic lives entirely in services.

### 2.9 Custom exception hierarchy
`NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `BusinessRuleError`, `ConflictError`, all extending `AppError`. Global handlers convert to HTTP responses. Routes never raise `HTTPException` directly. Services wrap mutations in try/except with `db.rollback()` on failure, then re-raise.
**Consistency fix applied:** `watchlist_service.get_watchlist_item_for_movie` originally returned `None` on a miss while `rating_service`'s equivalent raised `NotFoundError` — made consistent, both raise now.

### 2.10 `poster_path = ""` sentinel
`NULL` = not yet enriched, `""` = confirmed unmatched on TMDB, real value = enriched. `_enriched_only()` filters both `NULL` and `""` out of public movie endpoints.
**Real bug fixed:** TMDB `401` (bad credentials) was originally treated as retryable, silently and permanently mismarking real movies as unmatched. Now fails the whole script immediately on `401`.

### 2.11 `utcnow()` helper
Defined in `models.py`, used as the default for all datetime columns — timezone-aware UTC throughout.

### 2.12 Admin authorization
`users.role` enum, default `user`. No self-serve admin-creation endpoint — first admin promoted via direct SQL. `require_admin` dependency layers on `get_current_user`. Applied to `POST /movies`, `POST /genres` only.

### 2.13 Refresh tokens: Postgres, not Redis
Deferred — Redis not used elsewhere yet. Revisit once Redis exists for caching/BullMQ.

### 2.14 Login: JSON body, not OAuth2 form
Consistent with the rest of the API. Tradeoff: Swagger's Authorize button doesn't auto-wire.

### 2.15 Frontend design system — full redesign, second pass
First version (warm/cream/film-catalog aesthetic) assessed as reading dated. Replaced with near-white/near-black cool palette, coral-red accent, `Instrument Serif`/`Geist`/`Geist Mono`, a real elevation/shadow system, and a proper `Button` component (solid/outline/ghost). Semantic-token discipline meant the full redesign only touched `globals.css` + font imports.
Also explored and **deliberately dropped**: poster-color-extraction + per-genre theming.

### 2.16 Test database: separate Postgres instance, not SQLite
Chosen specifically because the schema leans on Postgres-native features (`Enum` columns, `ondelete="CASCADE"`) that SQLite emulates poorly or ignores. `movie_db_test`, same local Postgres instance. Tests run inside a transaction + SAVEPOINT per test so service-level `commit()` calls don't leak data between tests.

### 2.17 Recommendation features — three distinct surfaces, mapped to techniques
Decided the product will expose three separate recommendation surfaces, each backed by a different technique:
| Feature | Technique | Depends on |
|---|---|---|
| "Users with similar taste" | Pure collaborative filtering | CF model (Milestone 4 — **in progress**) |
| "Because you liked X" | Pure content-based filtering | Genre/metadata similarity (Milestone 4/5, not started) |
| "You may like" | Hybrid | Both of the above blended (Milestone 5) |

Build order follows the dependency chain — CF first (unlocks a shippable feature on its own), then content-based, then the hybrid blend.

### 2.18 CF training data: filtered to movies with ≥5 ratings
Raw `ml-20m`: 26,744 movies, 20,000,263 ratings. Movies with <5 ratings give CF almost no signal to learn from. Filtered to movies with ≥5 ratings: **18,345 movies retained (68.6%), 19,984,024 ratings retained (99.92%)** — a clean cut, trims long-tail catalog noise while losing almost no actual signal. Movies below this threshold remain fully visible/searchable in the app; they're served by content-based filtering (Milestone 5), not CF — this is the intended two-stage design, not a gap.

---

## 3. Database Schema

**`genres`** — id, name (unique), slug (unique), created_at

**`movies`** — id, tmdb_id (unique, canonical), imdb_id, movielens_id, title, original_title, tagline, description, runtime, released_on, poster_path (sentinel), backdrop_path, original_language, status (enum), budget, revenue, adult, tmdb_vote_average, tmdb_vote_count, trailer_link (**column exists, never populated**), created_at, updated_at (utcnow)

**`movie_genres`** — pure junction

**`people`**, **`movie_cast`**, **`platforms`**, **`movie_platforms`** — schema built, **no routes yet**

**`users`** — id, email (unique, NOT NULL), username (unique, NOT NULL), name, role (enum), is_seed_user (bool), timestamps

**`user_credentials`** — one-to-one, optional (absence = cannot log in)

**`oauth_accounts`** — deferred, not built

**`refresh_tokens`** — token_hash (SHA-256), expires_at, revoked_at (nullable = valid)

**`ratings`** — user_id, movie_id, rating (0.5–5.0), rated_at, updated_at. Unique (user_id, movie_id). Cascade delete both FKs.

**`watchlist_items`** — user_id, movie_id, status (enum), added_at, watched_at (set once, first transition only). Unique (user_id, movie_id). Cascade delete both FKs.

---

## 4. Backend — Current State

### Fully built, tested (unit + integration)
- **`genres`** — CRUD, admin-gated creation
- **`movies`** — CRUD, search (contains-match, fixed from an accidental prefix-only regression), genre filter, pagination, admin-gated creation, `attach_image_urls()`, `_enriched_only()` filtering. Sorting not yet added.
- **`auth`** — signup, login, JWT access tokens, refresh token rotation (atomic, single-commit), server-side logout/revocation, `get_current_user`, `require_admin`. Route-level dead code (leftover `if not result` checks from before the exception-hierarchy refactor) found and removed.
- **`ratings`** — CRUD, upsert-on-repeat-rate, strictly owned by `current_user.id`
- **`watchlist`** — CRUD, add/status-update/remove, `joinedload` to avoid N+1, `watched_at` set-once semantics

### Real bugs found and fixed during this build (worth keeping visible — this is genuine engineering signal)
- `create_movie`'s `payload.model_dump(exclude="genre_ids")` — passed a bare string instead of a set to `exclude`, meaning `genre_ids` wasn't actually excluded and `Movie(**data)` would receive an invalid keyword argument. Caught by a dedicated test (`test_create_movie_with_genres_succeeds`) that would have failed against the old code.
- Movie search regressed from contains-match (`%q%`) to prefix-only (`q%`) at some point — caught during a review pass, confirmed intended behavior, fixed and locked in with a test.
- TMDB enrichment script treated `401` as retryable, silently corrupting real "not found" data on auth failures — fixed to fail fast.
- `watchlist_service`/`rating_service` inconsistency on not-found behavior (`None` vs. raise) — unified.
- Several stale `X | None` return type annotations on functions that actually always raise instead of returning `None` — cleaned up across `rating_service`, `watchlist_service`, `movie_service`.

### Test coverage
- **Unit tests:** `rating_service`, `watchlist_service`, `auth_service`, `movie_service` — all core business logic covered
- **Integration tests:** `test_movies_api.py`, `test_ratings_api.py`, `test_watchlist_api.py`, `test_auth_api.py` — real HTTP requests via FastAPI `TestClient`, covering auth enforcement, admin gating, ownership isolation, real status codes, and (critically) real refresh-token rotation/reuse-rejection via actual cookies
- Test DB: separate Postgres instance (`movie_db_test`), transactional isolation per test

### Not yet built
- MovieLens seed-user + seed-ratings bulk scripts (schema ready, scripts not written — needs real bulk-insert engineering for ~20M rows)
- `trailer_link` population
- `people`/`platforms`/`movie_cast` routes
- OAuth providers
- Sorting on movie list endpoint
- Rate limiting on `/auth/login` (known gap — explicitly parked until after ML work, per user request, to be revisited)

---

## 5. Frontend — Current State

### Fully built & tested
- Design system: near-white/near-black palette, coral-red accent, `Instrument Serif`/`Geist`/`Geist Mono`, elevation system, `Button` component
- API client layer + types for auth, movies, genres, ratings, watchlist
- `AuthContext` (in-memory `access_token`, snake_case — deliberate deviation from camelCase convention), silent session restore via refresh cookie
- `useGuestOnly` hook
- `Navbar` (sticky, backdrop-blur, `/movies` + conditional watchlist link), `Logo`, `BackButton`
- `/login`, `/signup` — full validation, real backend error surfacing
- `/movies` (browse) — search + genre filter + infinite scroll (generation-counter pattern, `AbortController` tried and abandoned as unreliable)
- `/movies/[id]` (detail) — backdrop hero, full metadata, `RatingWidget` + `WatchlistButton` with optimistic updates + rollback
- `/watchlist` — protected page, status filters, optimistic updates
- `RatingWidget` — half-star precision, optimistic updates, logged-out state
- `WatchlistButton` — three-state, optimistic updates, logged-out state

### Not yet built
- Cast/recommendations sections on detail page (blocked on backend `people`/`movie_cast` and the recommender)
- Sorting controls on `/movies`
- Any UI for the three recommendation surfaces (§2.17) — blocked on Milestone 4/5 backend work

---

## 6. ML / Recommendation Engine — Current State (Milestone 4, in progress)

### Done
- Data exploration: sparsity (99.46%), ratings-per-user and ratings-per-movie distributions analyzed, both confirmed strongly right-tailed
- Filtering decision made and validated: ≥5 ratings/movie threshold (§2.18)
- First trained model: SVD via `scikit-surprise`, `n_factors=50`, `n_epochs=5` (deliberately low for fast iteration, not final)
- **RMSE: 0.8460** — within the healthy expected range (0.80–0.90) for this dataset/approach
- Three-surface recommendation architecture decided (§2.17)

### In progress
- Precision@k / recall@k implementation written, **results not yet obtained** — this is the metric that actually validates recommendation *quality*, not just rating-prediction accuracy, and is required before calling Milestone 4's CF component done
- Hyperparameter tuning not yet started (current `n_epochs=5` is an iteration-speed choice, not a final one — a longer final run is expected once hyperparameters are settled)

### Not started
- Content-based filtering (genre/metadata similarity) — powers "Because you liked X"
- Hybrid blending — powers "You may like"
- Wrapping the validated model as a FastAPI route (`app/ml/`)
- Frontend integration of any recommendation rail
- MLflow/experiment tracking (Milestone 5 per original plan)
- Cold-start handling for real (non-seed) new users

---

## 7. Open Decisions / Things to Revisit

- **MovieLens seed-user + seed-ratings bulk scripts** — schema ready, scripts not built. Needed before CF can be trained on live-DB data rather than the raw CSV, and before real+seed rating blending is possible.
- **Model training data source, finalized** — currently training directly against MovieLens `ratings.csv`. Decision on when/whether to retrain against live DB data (real + seed blended) once the bulk scripts exist — not yet made.
- **Rate limiting on `/auth/login`** — known gap, explicitly deferred until after ML work per direct request. **Remember to raise this again once Milestone 4/5 wraps.**
- **`trailer_link`** — known gap, not scheduled.
- **First-admin bootstrapping** — manual SQL only.

---

## 8. Milestone Status

| Milestone | Status |
|---|---|
| 0 — Foundations | ✅ Done |
| 1 — Data Pipeline | 🔄 Movies + genres seeded & enriched (verified live). Seed-user/ratings bulk scripts still open. |
| 2 — Backend MVP | ✅ Done — auth, movies, genres, ratings, watchlist, custom exception hierarchy, full test coverage (unit + integration) |
| 3 — Frontend MVP | ✅ Done — auth, browse, detail, watchlist page, full design system |
| 4 — Recommendation Engine v1 | 🔄 **In progress** — CF model trained (RMSE 0.846), precision@k/recall@k pending, not yet wrapped as a service |
| 5 — Recommendation Engine v2 (hybrid + cold start) | ⏳ Not started |
| 6 — AI Automation (notifications) | ⏳ Not started |
| 7 — Testing Hardening | 🔄 Partially absorbed early — core unit/integration coverage already exists ahead of schedule. Coverage-gap review, TMDB mocking, and load testing still open. |
| **7.5 — Adversarial Security Review** *(new milestone, added mid-project)* | ⏳ Not started — deliberately deferred until after ML work. Planned scope: auth/session attacks, IDOR/authorization bypass, injection, brute-force/rate-limiting on login, CORS, error-message leakage, dependency audit. Findings + fixes to feed directly into Milestone 8's CI/CD pipeline. |
| 8 — Containerization & CI/CD | ⏳ Not started. Scope now expanded beyond the original plan: lint → test → **security scan** → build → push. |
| 9 — Kubernetes & Observability | ⏳ Not started |
| 10 — Polish & Resume Packaging | ⏳ Not started |

---

## 9. ADRs Written

- `docs/decisions/001-movie-id-strategy.md`
- `docs/decisions/002-single-fastapi-service.md`
- `docs/decisions/003-seed-user-reconsideration.md`

---

## 10. What This Project Currently Demonstrates (resume-relevant, and honestly earned)

- Full-stack ownership: schema design → migrations → service-layer business logic → REST API → typed frontend client → polished UI, all self-built
- Real security engineering: JWT + rotating/revocable refresh tokens, httpOnly cookies, role-based authorization, password hashing — not just "added a login page"
- Genuine test discipline: unit + integration coverage built *during* development, not bolted on after, including tests that catch real regressions (e.g. the search-behavior regression, the `exclude` bug)
- Debugging real, non-obvious production-style bugs: a silently-corrupting data pipeline bug, a type-mismatch bug in Pydantic's `exclude` API, several frontend race conditions
- Applied ML: trained and evaluated a real collaborative-filtering model against a genuinely large dataset (20M ratings), with both accuracy (RMSE) and relevance (precision@k, in progress) evaluation — not just calling `.fit()` and stopping
- Engineering judgment under real constraints: multiple documented instances of making a decision, discovering it was wrong, and correctly reversing it without compromising the original goal (seed users, error handling consistency, search behavior)

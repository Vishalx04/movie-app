# 001 — tmdb_id as Canonical Movie Identifier

## Status
Accepted

## Context
The app blends two data sources per movie: MovieLens (historical ratings,
synthetic `movieId`) and TMDB (live metadata — posters, overviews, release
dates, cast). Something has to be the primary key clients and internal
code refer to a movie by.

## Decision
`tmdb_id` is the canonical identifier for every movie going forward.
`movielens_id` is stored (nullable, unique) but used *only* to join
historical MovieLens ratings during offline model training — it is never
exposed in API responses and never used for lookups.

## Reasoning
- TMDB is the live, ongoing data source (posters, cast, upcoming releases).
  MovieLens is a static historical snapshot that stops updating.
- Movies added after the MovieLens dataset was frozen (anything recent)
  will only ever have a `tmdb_id`, never a `movielens_id` — so the
  canonical ID has to be the one guaranteed to exist for *every* movie,
  not just the seeded historical ones.
- Movies whose MovieLens `movieId` doesn't resolve to a valid `tmdb_id`
  (deprecated/missing links in `links.csv`) are skipped entirely during
  seeding rather than inserted with a null canonical ID — keeps the
  invariant "every row has a real tmdb_id" unconditionally true.

## Consequences
- The MovieLens → TMDB join (`links.csv`) is a one-time seeding-time
  concern, not something the running application ever has to reason
  about.
- If the app ever needs to re-attach to a different metadata provider,
  only the enrichment job changes — `tmdb_id` as the schema's backbone is
  unaffected.
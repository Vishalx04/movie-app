# 003 — MovieLens Seed Users: Rejected, Then Reconsidered

## Status
Accepted (revised from an earlier decision within the same project)

## Context
MovieLens's ~138,000 synthetic `userId`s need to exist as `users` rows
for historical ratings to be seeded via a normal foreign key — or the
recommender has zero bootstrap data until real users generate enough
ratings on their own.

## First decision (superseded)
Initially, seed users were rejected entirely. `users.email` and
`users.username` were made `NOT NULL`, and the table was scoped to
contain *only* real, authenticated signups — reasoning that a table full
of accounts with no way to log in undermined the invariant "every row in
`users` is a real account."

## Revised decision
Seed users were reintroduced, but in a way that preserves the original
safety property through a different mechanism:
- `is_seed_user: bool` flag, default `False`
- Deterministic, honestly-synthetic identity per seed row (not
  AI-generated fake-realistic data, which was explicitly rejected as
  *worse* — it would look real without being real)
- `email`/`username` stay `NOT NULL` and unique, satisfied honestly by
  the synthetic values — no schema weakening
- **No `user_credentials` row is created for seed users.** This, not
  nullable fields, is what makes login structurally impossible: the
  login flow already requires a `user_credentials` row to exist before
  password verification can even be attempted.

## Reasoning for the reversal
- The real goal of the original constraint was "nobody can log in as an
  account they don't own" — not literally "every row has real contact
  info." Once that distinction was clear, seed users could be
  reintroduced without weakening the actual safety property.
- MovieLens ratings give the collaborative-filtering model real
  bootstrap data from day one, rather than an empty recommender until
  organic usage accumulates — a real cold-start problem the first
  decision had created for the project as a whole, not just new users.

## Status of implementation
`is_seed_user` column and the `Rating` model/migration exist. The bulk
seed scripts (138K synthetic users, followed by a filtered subset of
MovieLens `ratings.csv`) are **not yet built** — this ADR reflects the
schema-level decision; the data pipeline work is tracked separately.
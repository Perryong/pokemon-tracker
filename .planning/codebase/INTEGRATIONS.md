# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

**Card Data API:**
- Pokémon TCG API - Retrieves sets, cards, and card details for the app UI
  - Evidence: `src/lib/api.ts` (`BASE_URL = 'https://api.pokemontcg.io/v2'`, hooks `useSets`, `useCards`, `useCard`)
  - SDK/Client: Native browser `fetch` (no dedicated SDK package)
  - Auth: API key sent in `X-Api-Key` header in `src/lib/api.ts`

**UI Attribution/External Link:**
- Pokémon TCG website link for attribution/outbound navigation
  - Evidence: `src/components/Navbar.tsx` (`href="https://pokemontcg.io"`)
  - SDK/Client: Not applicable
  - Auth: Not applicable

## Data Storage

**Databases:**
- Supabase Postgres schema defined via SQL migrations
  - Evidence: `supabase/migrations/20250518150840_sunny_scene.sql`, `supabase/migrations/20250518150930_empty_silence.sql`
  - Connection: Environment variables present by name (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) in root `.env` file
  - Client: Not detected in runtime code (`src/` has no Supabase client initialization/import)

**File Storage:**
- Local filesystem only for build/runtime assets (no cloud object storage integration detected in `src/`)

**Caching:**
- Browser localStorage used for client-side persistence
  - Evidence: `src/lib/collection.ts` (`localStorage` collection persistence), `src/components/Navbar.tsx` (theme persistence)

## Authentication & Identity

**Auth Provider:**
- Supabase Auth implied in database policies/triggers
  - Evidence: `auth.uid()` RLS policies and `auth.users` trigger references in `supabase/migrations/*.sql`
  - Implementation: Database-level RLS and trigger-based user profile creation; no frontend auth flow detected in `src/`

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Datadog/Bugsnag SDKs detected in `package.json` or `src/`)

**Logs:**
- Console logging in API layer
  - Evidence: `src/lib/api.ts` uses `console.error` for API/network errors and `console.log` for retry attempts

## CI/CD & Deployment

**Hosting:**
- Not explicitly configured (no platform-specific config files detected; app is built as Vite static output to `dist/`)

**CI Pipeline:**
- None detected (no `.github/workflows/`, no pipeline configs in repository root)

## Environment Configuration

**Required env vars:**
- `VITE_SUPABASE_URL` (name present in `.env`)
- `VITE_SUPABASE_ANON_KEY` (name present in `.env`)
- No runtime use of `import.meta.env` detected in `src/`; Pokémon TCG API key is hardcoded in `src/lib/api.ts`

**Secrets location:**
- Root `.env` file present for environment configuration
- Additional secret-bearing values may also exist in code constants (API header key in `src/lib/api.ts`)

## Webhooks & Callbacks

**Incoming:**
- None detected in frontend code (`src/`) and repository configs

**Outgoing:**
- HTTP requests to Pokémon TCG API via `fetch` in `src/lib/api.ts`

---

*Integration audit: 2026-03-20*

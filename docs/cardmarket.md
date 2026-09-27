# Cardmarket price source

Set `PTCG_API_KEY` in `.env.local` (ignored by Git) or the server environment. Never use a `VITE_` variable for this key.

`npm run dev` and `npm run preview` install the server middleware at `/api/cardmarket/:cardId`. After building, the browser requests this same-origin endpoint; it never contacts the authenticated provider directly. A static-only deployment cannot supply this endpoint: its host must run an equivalent server function using `server/cardmarket.ts`. Vite preview is for local build verification.

Opening a card requests its existing ID from pokemontcgapi.com. Responses must match the canonical or legacy ID. Only English, ungraded Cardmarket EUR rows are used; condition, printing, pricing basis and observation date are retained. Prices are converted to SGD with the existing dated ECB reference rate. TCGdex remains the fallback for missing cards, missing prices and provider failures. The UI labels which data source was used.

Successful and not-found responses are cached for six hours, capped at 512 cards per server process. Concurrent requests for the same card share one upstream request. A process-wide limit of 20 uncached calls per minute protects trial credits; production deployments should additionally enforce access controls and shared quotas appropriate to their users. No full-catalogue preload is performed. The provider charges two credits for a single-card request with prices; coverage and plan limits can still leave some cards without prices.

Reference: https://pokemontcgapi.com/docs/api/cards/get

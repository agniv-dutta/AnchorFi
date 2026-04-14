# AnchorFi Submission Todo (Tomorrow EOD)

Status legend:
- [x] done
- [~] in progress
- [ ] pending

## P0 Must-Have (Stability + Credibility)

1. [x] Enforce startup runtime config validation for production/staging.
2. [x] Add provider health matrix endpoint for Groq/DefiLlama/Etherscan/GoPlus.
3. [x] Add structured assessment logs with latency, cache hit, provider, fallback flag.
4. [x] Include data freshness metadata in assess response.
5. [ ] Add API contract tests for /api/assess, /api/compare, /api/watchlist, /api/report/{id}.
6. [ ] Add risk scorer unit tests for threshold boundaries and exploit override.
7. [ ] Add compare rendering regression check (response shape + frontend mapping).
8. [ ] Add explicit startup warning banner if app is running with fallback AI mode.

## P1 Data Quality + Explainability

9. [ ] Add confidence degradation rules when key sources are missing.
10. [ ] Add contribution breakdown fields for each risk dimension in response payload.
11. [ ] Add source-level fetch timestamps (Groq, DefiLlama, Etherscan, GoPlus).
12. [ ] Add partial_data_flags in compare response card-level summaries.
13. [ ] Add incident knowledge list expansion beyond Ronin exploiter.
14. [ ] Add protocol alias normalization table for top 25 DeFi protocols.
15. [ ] Add deterministic fallback quality templates per risk band (low/med/high).
16. [ ] Add sanity clamps for impossible provider values before scoring.

## P1 UX + Product Readiness

17. [ ] Add per-widget loading and error states in compare panel.
18. [ ] Add explicit data-source badges (Live, Partial, Cached, Fallback) in UI.
19. [ ] Add fallback/AI provider badge in AI assessment panel.
20. [ ] Add watchlist risk-change percentage indicator, not only up/down boolean.
21. [ ] Add mobile compare layout refinement for 2- and 3-card sets.
22. [ ] Add report copy-to-link confirmation persistence on share route.

## P2 Ops + Delivery

23. [ ] Add pytest and CI command docs to README.
24. [ ] Add one-command local verify script (backend compile + frontend build + API smoke).
25. [ ] Add .env.example strictness notes for APP_ENV and provider keys.
26. [ ] Add submission runbook section: known limitations + demo script.
27. [ ] Add chunk-size optimization pass for frontend build warning.
28. [ ] Add optional Sentry/OpenTelemetry hooks for post-demo diagnostics.

## Implemented This Session

- Runtime validation in backend config/startup.
- Provider health matrix endpoint: GET /api/health/providers.
- Structured assessment logs with latency/cache/provider/fallback metadata.
- Data freshness block in assess payload:
  - fetched_at
  - source_age_seconds
  - partial_data_flags

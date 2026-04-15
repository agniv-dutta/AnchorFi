<h1 align="center">AnchorFi</h1>

<p align="center">
  AnchorFi: instant DeFi insurance risk assessment with explainable scoring, on-chain + protocol intelligence, and premium estimation.
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" />
  <img alt="Frontend" src="https://img.shields.io/badge/Frontend-React-20232A?logo=react&logoColor=61DAFB" />
  <img alt="Bundler" src="https://img.shields.io/badge/Bundler-Vite-646CFF?logo=vite&logoColor=white" />
  <img alt="Styling" src="https://img.shields.io/badge/Styling-Plain_CSS-111111" />
  <img alt="Charts" src="https://img.shields.io/badge/Charts-Recharts-FF7043" />
  <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
</p>

## What This Project Does

AnchorFi helps evaluate DeFi risk quickly for either:
- an Ethereum contract address (for example `0x...`), or
- a protocol identifier/name (for example `aave`).

It combines:
- On-chain contract and security signals,
- Protocol-level TVL/age/audit/hack context,
- Weighted risk scoring by category,
- Score contribution breakdown by weighted dimension,
- Source freshness metadata + per-provider timestamps,
- Dynamic premium estimation,
- Groq-generated underwriter narrative,
- Protocol comparison (up to 3),
- Watchlist monitoring with risk-increase and risk-change percentage,
- Shareable report links.

The output is intentionally understandable by non-specialists while still preserving raw signals for technical inspection.

---

## Tech Stack

### Backend
- FastAPI (REST API)
- Pydantic v2 (validation + schemas)
- SQLAlchemy async + aiosqlite (persistence)
- httpx (external API calls)
- Uvicorn (ASGI server)

### Frontend
- React 18
- Vite 5
- Plain CSS (brutalist design system)
- Recharts (radar, timeline, comparison charts)

### Data Sources / External APIs
- Etherscan API (contract/source/transaction metadata)
- GoPlus API (contract security flags)
- DefiLlama API (protocol and hacks data)
- AI provider: Groq (`llama-3.3-70b-versatile`)

---

## Repository Structure

```text
riskless/
  backend/
    core/
    models/
    routers/
    services/
    main.py
    requirements.txt
  frontend/
    src/
      components/
    package.json
```

---

## How The System Works

1. User submits a target + coverage inputs.
2. Backend checks same-target same-day cache from SQLite.
3. Backend fetches blockchain + protocol signals concurrently.
4. Scoring engine computes:
   - code risk,
   - liquidity risk,
   - team risk,
   - track record,
   and a weighted composite score.
5. Premium engine estimates a USDC premium with score and term.
6. Groq AI creates plain-English underwriting notes.
7. Assessment emits explainability metadata (`score_breakdown`) plus freshness metadata (`data_freshness`).
8. Assessment is saved and exposed to history/report/watchlist features.

---

## Environment Configuration

Create `riskless/backend/.env` (copy from `riskless/backend/.env.example`) and set values:

```env
APP_ENV=development
GROQ_API_KEY=
ETHERSCAN_API_KEY=
DATABASE_URL=sqlite+aiosqlite:///./anchorfi.db
```

### Required vs Optional

- Optional but recommended:
  - `GROQ_API_KEY` for AI explanation text
  - `ETHERSCAN_API_KEY` for richer address-level signals
- Required:
  - `DATABASE_URL`
- Runtime guardrails:
  - `APP_ENV=production|staging` requires `GROQ_API_KEY` at startup

Frontend uses Vite proxy (`/api` -> `http://localhost:8000`) from `riskless/frontend/vite.config.js`.

---

## Run Locally (Windows)

### 1) Backend

```powershell
cd riskless
..\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
..\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2) Frontend

Open a second terminal:

```powershell
cd riskless/frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

---

## API Documentation

When backend is running:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Base URL

`http://127.0.0.1:8000/api`

### 1) Health Check

- Method: `GET`
- Path: `/health`

Example response:

```json
{
  "status": "ok",
  "timestamp": "2026-04-14T06:07:54.289680+00:00"
}
```

Provider health matrix:

- Method: `GET`
- Path: `/health/providers`

Includes provider reachability, latency, HTTP status, and key-presence flags.

### 2) Risk Assessment

- Method: `POST`
- Path: `/assess`

Request body:

```json
{
  "target": "aave",
  "coverage_amount": 10000,
  "coverage_days": 30
}
```

Response includes:
- `id`, `target`, `created_at`
- `code_risk`, `liquidity_risk`, `team_risk`, `track_record`
- `composite_risk_score`
- `score_breakdown` (weighted explainability contributions)
- `premium`, `coverage_amount`, `coverage_days`
- `ai` (Groq narrative)
- `data_freshness` (`fetched_at`, `source_age_seconds`, `partial_data_flags`, `source_timestamps`)
- `raw_signals`
- `cached`

Example assess response excerpt:

```json
{
  "target": "aave",
  "composite_risk_score": 23,
  "score_breakdown": {
    "code_risk": {"score": 30, "weight": 0.35, "weighted_points": 10.5},
    "liquidity_risk": {"score": 20, "weight": 0.25, "weighted_points": 5.0},
    "team_risk": {"score": 30, "weight": 0.25, "weighted_points": 7.5},
    "track_record": {"score": 0, "weight": 0.15, "weighted_points": 0.0},
    "total_weighted_points": 23.0
  },
  "ai": {
    "confidence": "Medium",
    "ai_provider": "groq"
  },
  "data_freshness": {
    "fetched_at": "2026-04-15T16:47:39.559951+00:00",
    "source_age_seconds": 0,
    "partial_data_flags": [],
    "source_timestamps": {
      "defillama": "2026-04-15T16:47:39.559951+00:00",
      "etherscan": null,
      "goplus": null,
      "groq": "2026-04-15T16:47:39.559951+00:00",
      "scoring": "2026-04-15T16:47:39.559951+00:00"
    }
  }
}
```

### 3) History

- Method: `GET`
- Path: `/history`
- Query: `limit` (default 20)

### 4) Compare Targets

- Method: `POST`
- Path: `/compare`

Request body:

```json
{
  "targets": ["aave", "compound", "uniswap"],
  "coverage_amount": 10000,
  "coverage_days": 30
}
```

Returns:
- `results`: array of assessments
- `recommended`: safest target by lowest composite score

Each result also carries:
- `data_freshness` metadata for partial-data visibility in compare cards
- `score_breakdown` for per-dimension explainability

### 5) Report

- Method: `GET`
- Path: `/api/report/{id}` (JSON API response)
- Method: `GET`
- Path: `http://127.0.0.1:8000/report/{id}` (shareable HTML page)

### 6) Watchlist

- Method: `POST`
- Path: `/watchlist`
- Body: `{"address":"0x..."}`

- Method: `GET`
- Path: `/watchlist`

- Method: `GET`
- Path: `/watchlist/refresh`

Refresh response includes `risk_change_pct` alongside `previous_score` and `latest_score`.

Example refresh response excerpt:

```json
{
  "items": [
    {
      "address": "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
      "previous_score": 95,
      "latest_score": 95,
      "risk_change_pct": 0.0,
      "risk_increased": false
    }
  ]
}
```

- Method: `DELETE`
- Path: `/watchlist/{address}`

### Curl Examples

```bash
BASE_URL="http://127.0.0.1:8000/api"
```

Health:

```bash
curl -X GET "$BASE_URL/health"
```

Assess:

```bash
curl -X POST "$BASE_URL/assess" \
  -H "Content-Type: application/json" \
  -d '{"target":"aave","coverage_amount":10000,"coverage_days":30}'
```

Compare:

```bash
curl -X POST "$BASE_URL/compare" \
  -H "Content-Type: application/json" \
  -d '{"targets":["aave","compound","uniswap"],"coverage_amount":10000,"coverage_days":30}'
```

Watchlist add:

```bash
curl -X POST "$BASE_URL/watchlist" \
  -H "Content-Type: application/json" \
  -d '{"address":"0x098B716B8Aaf21512996dC57EB0615e2383E2f96"}'
```

---

## Frontend Features

- Brutalist visual system (cream background, black borders, hard shadows, no rounded corners)
- Sequential loading state
- Animated score gauge + risk bars
- AI panel with confidence and verdict
- Radar chart for 4 risk dimensions
- Timeline chart when protocol appears multiple times in history
- Comparison panel with safest badge and grouped bar chart
- Comparison panel with loading/error states and source/partial-data badges
- Watchlist panel with risk increase detection and risk-change percentage indicator
- Recent assessments table with click-to-reassess
- Demo quick buttons:
  - TRY: AAVE
  - TRY: COMPOUND
  - TRY: RONIN BRIDGE EXPLOITER

---

## Notes and Limitations

- Ethereum mainnet focused in current implementation.
- Data quality depends on upstream API availability and rate limits.
- If Groq is unavailable, the API returns a structured deterministic AI placeholder.
- AI confidence is degraded when critical data sources are partial/missing.
- This is a risk analytics demo, not financial, legal, or insurance underwriting advice.

---

## Quick Troubleshooting

1. Backend fails to start
- Ensure virtual environment Python is used:
  `..\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`

2. Frontend cannot reach backend
- Verify backend is running on `127.0.0.1:8000`.
- Keep Vite proxy enabled in `riskless/frontend/vite.config.js`.

3. AI block is missing
- Set `GROQ_API_KEY` in `riskless/backend/.env`.

4. Weak on-chain signals
- Add valid `ETHERSCAN_API_KEY` and retry with a known Ethereum contract address.

---

## License

No license file is currently included. Add one if you plan to distribute publicly.

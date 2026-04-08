<h1 align="center">AnchorFi</h1>

<p align="center">
  AnchorFi: instant DeFi insurance risk assessment with explainable scoring, on-chain + protocol intelligence, and premium estimation.
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" />
  <img alt="Frontend" src="https://img.shields.io/badge/Frontend-React-20232A?logo=react&logoColor=61DAFB" />
  <img alt="Bundler" src="https://img.shields.io/badge/Bundler-Vite-646CFF?logo=vite&logoColor=white" />
  <img alt="Styling" src="https://img.shields.io/badge/Styling-Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white" />
  <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
</p>

## What This Project Does

AnchorFi helps evaluate DeFi risk quickly for either:
- an Ethereum contract address (for example `0x...`), or
- a protocol identifier/name (for example `aave` or a DefiLlama protocol URL).

It combines:
- On-chain contract and security signals,
- Protocol-level TVL/age/audit/hack context,
- Weighted risk scoring by category,
- Dynamic premium estimation,
- Optional AI underwriter narrative.

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
- Tailwind CSS

### Data Sources / External APIs
- Etherscan API (contract/source/transaction metadata)
- GoPlus API (contract security flags)
- DefiLlama API (protocol and hacks data)
- AI provider (optional): Groq or Anthropic

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
    package.json
  anchorfi.sqlite3
  anchorfi_cache.sqlite3
```

---

## How The System Works

1. User submits a target + coverage inputs.
2. Backend aggregates data from on-chain and protocol services.
3. Scoring engine computes:
   - code risk,
   - liquidity risk,
   - team risk,
   - track record,
   and a weighted composite score.
4. Premium engine estimates a USDC-denominated premium using score and term.
5. Optional AI narrative creates plain-English underwriting notes.
6. Response is cached in memory and persisted in SQLite for daily reuse.

---

## Environment Configuration

Create `backend/.env` (copy from `backend/.env.example`) and set values:

```env
ANTHROPIC_API_KEY=
GROQ_API_KEY=
AI_PROVIDER=auto

ETHERSCAN_API_KEY=
GOPLUS_API_KEY=

SQLITE_PATH=anchorfi.sqlite3
```

### Required vs Optional

- Recommended for best results:
  - `ETHERSCAN_API_KEY`
  - `GOPLUS_API_KEY`
- Optional:
  - `GROQ_API_KEY` or `ANTHROPIC_API_KEY` for AI explanation text
- `AI_PROVIDER` values:
  - `auto` (prefers Groq if present, then Anthropic)
  - `groq`
  - `anthropic`
  - `none`

Frontend env (optional):

```env
VITE_API_BASE=http://127.0.0.1:8000
```

If `VITE_API_BASE` is not set, frontend defaults to `http://127.0.0.1:8000`.

---

## Run Locally (Windows)

### 1) Backend

```powershell
py -3.11 -m pip install -r riskless/backend/requirements.txt
cd riskless
py -3.11 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 2) Frontend

Open a second terminal:

```powershell
cd riskless/frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:5173`

---

## API Documentation

The backend automatically exposes interactive docs when running:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Base URL

`http://127.0.0.1:8000`

### 1) Health Check

- Method: `GET`
- Path: `/health`
- Purpose: quick liveness probe for backend availability.

Example response:

```json
{
  "status": "ok"
}
```

### 2) Risk Assessment

- Method: `POST`
- Path: `/assess`
- Purpose: compute risk profile and premium estimate for a target.

Request body:

```json
{
  "target": "aave",
  "coverage_amount": 10000,
  "coverage_days": 30
}
```

Field definitions:
- `target` (string, required):
  - Ethereum contract address (`0x...`) OR protocol name/slug/DefiLlama protocol URL.
- `coverage_amount` (number, > 0): desired notional coverage.
- `coverage_days` (integer, 1..365): policy duration in days.
- `wallet_value` (number, optional, > 0): used by the AI recommendation engine to estimate how much of the wallet should be covered.

Response includes:
- target resolution info (`resolved`),
- category scores (`code_risk`, `liquidity_risk`, `team_risk`, `track_record`),
- weighted `composite_risk_score` (0-100),
- `premium_usdc` and `premium_details`,
- optional `ai` narrative,
- `report_uuid` for the shareable report page,
- `raw_signals` for transparency,
- `cached` boolean (daily cache hit indicator).

Representative response shape:

```json
{
  "report_uuid": "c1c6c5d8-1111-4d7a-9f2a-7e2a3c9a1c11",
  "target": "aave",
  "wallet_value": 50000,
  "resolved": {
    "is_address": false,
    "address": null,
    "protocol_slug": "aave"
  },
  "as_of": "2026-04-08T12:34:56.000000+00:00",
  "code_risk": { "score": 25, "flags": ["..."] },
  "liquidity_risk": { "score": 20, "flags": ["..."] },
  "team_risk": { "score": 30, "flags": ["..."] },
  "track_record": { "score": 18, "flags": ["..."] },
  "composite_risk_score": 24,
  "premium_usdc": 96.0,
  "premium_details": {
    "base_rate": 0.002,
    "risk_multiplier": 4.6,
    "uncapped_premium": 92.0,
    "cap": 2000.0,
    "capped": false
  },
  "ai": {
    "summary": "...",
    "top_risks": ["..."],
    "confidence": "Medium",
    "recommended_action": "Insure with caution",
    "recommended_coverage_percentage": 35,
    "recommended_coverage_amount": 17500
  },
  "raw_signals": {},
  "cached": false
}
```

### 3) Assessment History

- Method: `GET`
- Path: `/history`
- Query param:
  - `limit` (optional, default `25`, clamped between `1` and `200`)
- Purpose: fetch recent persisted assessments.

Example request:

`GET /history?limit=10`

Example response:

```json
{
  "items": [
    {
      "id": 1,
      "report_uuid": "c1c6c5d8-1111-4d7a-9f2a-7e2a3c9a1c11",
      "target": "aave",
      "as_of": "2026-04-08T12:34:56.000000+00:00",
      "composite_risk_score": 24,
      "premium_usdc": 96.0
    }
  ]
}
```

### 4) Compare Targets

- Method: `POST`
- Path: `/compare`
- Purpose: assess up to 3 targets side by side and identify the lowest-risk winner.

Request body:

```json
{
  "targets": ["AAVE", "Compound", "Uniswap"],
  "coverage_amount": 10000,
  "coverage_days": 30,
  "wallet_value": 50000
}
```

### 5) Shareable Report

- Method: `GET`
- Path: `/report/{uuid}`
- Purpose: return a minimal, read-only HTML page for a single assessment.
- Use the `report_uuid` from `/assess`, `/compare`, or `/history`.

### 6) Watchlist

- Method: `POST`
- Path: `/watchlist/{address}`
- Purpose: store an Ethereum contract address in the watchlist.

- Method: `GET`
- Path: `/watchlist`
- Purpose: re-assess all stored addresses and highlight any that increased by more than 10 points versus the previous cached score.

### Curl Examples

Set a base URL once:

```bash
BASE_URL="http://127.0.0.1:8000"
```

Health check:

```bash
curl -X GET "$BASE_URL/health"
```

Assess by protocol name:

```bash
curl -X POST "$BASE_URL/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "aave",
    "coverage_amount": 10000,
    "coverage_days": 30,
    "wallet_value": 50000
  }'
```

Compare three protocols:

```bash
curl -X POST "$BASE_URL/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["AAVE", "Compound", "Uniswap"],
    "coverage_amount": 10000,
    "coverage_days": 30,
    "wallet_value": 50000
  }'
```

Assess by Ethereum address:

```bash
curl -X POST "$BASE_URL/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "0x5a98fcbea516cf06857215779fd812ca3bef1b32",
    "coverage_amount": 25000,
    "coverage_days": 60
  }'
```

Get recent history:

```bash
curl -X GET "$BASE_URL/history?limit=10"
```

Open a report page:

```bash
curl -X GET "$BASE_URL/report/<report-uuid>"
```

Add an address to the watchlist:

```bash
curl -X POST "$BASE_URL/watchlist/0x5a98fcbea516cf06857215779fd812ca3bef1b32"
```

Refresh the watchlist:

```bash
curl -X GET "$BASE_URL/watchlist"
```

### Postman Collection

Create a file named `AnchorFi.postman_collection.json`, paste the JSON below, then import it in Postman.

```json
{
  "info": {
    "name": "AnchorFi API",
    "_postman_id": "8f1d2cae-3d4d-44f4-8dd4-9f1f97ef95f9",
    "description": "Requests for AnchorFi backend",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://127.0.0.1:8000"
    }
  ],
  "item": [
    {
      "name": "Health",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/health",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "health"
          ]
        }
      }
    },
    {
      "name": "Assess - Protocol",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"target\": \"aave\",\n  \"coverage_amount\": 10000,\n  \"coverage_days\": 30\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/assess",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "assess"
          ]
        }
      }
    },
    {
      "name": "Assess - Address",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"target\": \"0x5a98fcbea516cf06857215779fd812ca3bef1b32\",\n  \"coverage_amount\": 25000,\n  \"coverage_days\": 60\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/assess",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "assess"
          ]
        }
      }
    },
    {
      "name": "History",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/history?limit=10",
          "host": [
            "{{baseUrl}}"
          ],
          "path": [
            "history"
          ],
          "query": [
            {
              "key": "limit",
              "value": "10"
            }
          ]
        }
      }
    }
  ]
}
```

---

## Scoring Model (High-Level)

Composite risk score is a weighted blend:
- Code Risk: 35%
- Liquidity Risk: 25%
- Team Risk: 25%
- Track Record: 15%

Each category is normalized to an integer 0..100 and then combined.

Premium model (high level):
- Base rate: `0.2%` per 30 days,
- Risk multiplier increases with composite score,
- Duration adjusts proportionally,
- Final premium capped at `20%` of coverage amount.

This is a demo heuristic, not actuarial pricing advice.

---

## Caching and Persistence

- In-memory cache: keyed by `(target, day)` to avoid duplicate processing in-process.
- SQLite persistence: stores daily assessment snapshots and supports history endpoint.
- Duplicate protection: unique index on `(target, day)`.

---

## Notes and Limitations

- Ethereum mainnet focused in current implementation.
- Data quality depends on upstream API availability and rate limits.
- AI summary is optional and can be disabled.
- This is a hackathon/demo-style analytical tool, not investment or insurance advice.

---

## Quick Troubleshooting

1. Backend fails to start
- Ensure Python 3.11 is installed.
- Reinstall requirements from `backend/requirements.txt`.

2. Frontend cannot reach backend
- Verify backend is running on `127.0.0.1:8000`.
- Set `VITE_API_BASE` if backend URL differs.

3. AI block is missing
- Set `GROQ_API_KEY` or `ANTHROPIC_API_KEY` in `backend/.env`.
- Confirm `AI_PROVIDER` is not `none`.

4. Weak or empty on-chain signals
- Add valid `ETHERSCAN_API_KEY` and `GOPLUS_API_KEY`.
- Retry with known valid Ethereum address target.

---

## License

No license file is currently included. Add a project license if you plan to distribute publicly.

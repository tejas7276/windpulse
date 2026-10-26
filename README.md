# WindPulse

UK national wind generation, day-ahead forecast vs actual, for January 2026.

## 1. Overview and business problem

A UK electricity utility buys power on the wholesale day-ahead market. Wind output is a large and variable part of GB supply, so the wind forecast available at the time of purchase matters. WindPulse lets a procurement team pick a day in January 2026, see the wind forecast that was available the day before, compare it with what was actually generated, and see how accurate that forecast was.

It is a descriptive analysis tool. It does not know the utility's demand, market prices or other generation, so it does **not** calculate how much to buy, what it costs, or recommend trades.

## 2. Features

- Date picker restricted to 1–31 January 2026.
- Half-hourly chart of forecast (WINDFOR) vs actual (FUELHH) wind generation, in MW, UK local time.
- The forecast publication time actually used, and the decision cutoff it was selected against.
- MAE, RMSE, MAPE, average error (bias), over/under-forecast counts, matched/unmatched half-hours.
- Forecast-error bar chart (forecast − actual) and a table of half-hours with unusually large errors.
- A descriptive "shortfall" measure and a plain statement of what the app cannot tell you.
- Loading, empty and error states.

## 3. Tech stack

React 18 + Vite, Recharts · Python 3.12+, FastAPI, Pandas, Requests · Docker / Docker Compose · Vercel (frontend), Render (backend) · pytest.

## 4. Architecture

```
Browser (React) ──GET /api/wind/day?date=…──▶ FastAPI ──▶ Elexon BMRS API
                                              │            ├─ FUELHH (actuals)
                                              │            └─ WINDFOR (forecasts)
                                              └─ pandas: clean → select forecast → match → metrics → JSON
```

One endpoint returns everything the dashboard needs for a day, so the page makes a single request and Elexon is queried once per dataset per day (results are cached in memory for an hour).

## 5. The two Elexon datasets

Base URL: `https://data.elexon.co.uk/bmrs/api/v1`

| Dataset | Used for | Endpoint | Fields used |
| --- | --- | --- | --- |
| **FUELHH** | Actual generation | `/datasets/FUELHH/stream` | `fuelType` (`WIND` only), `startTime`, `generation`, `publishTime` (to break ties) |
| **WINDFOR** | Forecast generation | `/datasets/WINDFOR/stream` | `startTime`, `publishTime`, `generation` |

Query parameters used: FUELHH `settlementDateFrom`, `settlementDateTo`, `fuelType`; WINDFOR `publishDateTimeFrom`, `publishDateTimeTo`; both `format=json`.

> **Not verified in this build session.** The Elexon documentation pages render with JavaScript and could not be read, and the sandbox used to build this project could not reach `data.elexon.co.uk` (blocked by its network policy). The field names come from the assignment brief; the parameter names come from the author's recollection of the Elexon OpenAPI and are **unconfirmed**. The backend was tested only against a local stand-in server and unit-test fixtures, never against real Elexon data. Before relying on the app, run the check script described in [Verifying the Elexon integration](#verifying-the-elexon-integration).

Units: the app labels generation as **MW** on the assumption that both datasets report power in MW. This also needs confirming with the check script.

## 6. Method: choosing the forecast that was available

For a delivery date *D*:

1. **Decision cutoff** = `DAY_AHEAD_CUTOFF` (default **09:20**) UK local time on *D − 1*, converted to UTC with the `Europe/London` time zone (so it stays correct across the March/October clock changes; January is always GMT).
2. Request all WINDFOR publications with `publishTime` in the 72 hours up to the cutoff.
3. For every half-hour `startTime`, keep the **latest forecast whose `publishTime` ≤ cutoff**. Forecasts published after the cutoff are never used, even if that leaves a half-hour with no forecast.
4. Get FUELHH `WIND` actuals for *D*, and match them to forecasts on exact `startTime`.
5. Compute metrics on half-hours that have both values.

Cleaning rules: non-`WIND` rows dropped; rows with unparseable times or non-numeric generation dropped (counted); duplicate actuals for one half-hour → latest `publishTime` kept; duplicate forecast rows (same `startTime` and `publishTime`) collapsed; forecast rows with no `publishTime` are dropped because their availability can't be established. Counts are returned in the API response under `coverage`.

If fewer than 12 half-hours match (`MIN_MATCHED_PERIODS`), accuracy metrics are withheld and the page says why.

### Decision cutoff: what is and isn't verified

The cutoff is the weakest-evidenced part of the project. Two market-operator pages were found:

- EPEX SPOT's trading brochure (June 2022) lists the GB 60-minute day-ahead auction at **09:20** and the 30-minute auction at 15:30, with times given as GMT.
- Nord Pool's N2EX support page gives gate closure at **09:50** GMT, with results by 10:00.

These disagree, both may be out of date, and neither was cross-checked against a current Elexon or market-operator source. The default of 09:20 is the earlier of the two, so no forecast published after either time is used. **Confirm the correct time for your market and set `DAY_AHEAD_CUTOFF` accordingly.** It is a configuration value, not a hard-coded rule.

## 7. Definitions

- **Forecast error** = forecast − actual (MW). Positive = over-forecast; negative = under-forecast.
- **MAE** = mean of |error|.
- **RMSE** = √ mean of error².
- **MAPE** = mean of |error| ÷ actual × 100, over half-hours where actual ≠ 0. Zero-actual half-hours are excluded because the ratio is undefined; the number used is shown.
- **Average error (bias)** = mean of error.
- **Shortfall** = max(actual − forecast, 0), per the project brief. Note this is positive when the forecast was *too low* (actual exceeded forecast). Total shortfall energy (MWh) = Σ shortfall MW × 0.5 h.
- **Large error**: |error| greater than 1.5 × that day's MAE. A simple relative rule, not a statistical test.

## 8. Assumptions and limitations

- Cutoff time is an assumption (see above).
- Generation units, WINDFOR resolution (it may not publish every half-hour, which would show up as unmatched periods) and API parameter names are unconfirmed against the live API.
- National totals only; no demand, prices, dispatch, interconnectors or other fuels.
- Metrics are per-day. No multi-day aggregation.
- In-memory cache: lost on restart and not shared between instances.
- On a free hosting tier the backend may sleep and take a while to wake on the first request (check your host's current terms).
- Tested on Python 3.13 locally; the Docker image uses 3.12. Recharts 2.x is used (the 2.x branch is flagged as no longer active by npm).

## 9. Project structure

```
windpulse/
├── README.md
├── docker-compose.yml        # runs backend (8000) and frontend (3000)
├── render.yaml               # Render blueprint for the backend
├── .env.example              # optional compose overrides
├── .gitignore
├── docs/
│   └── VIDEO_SCRIPT.md       # timed two-part demo script and checklist
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt / requirements-dev.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, generic 500 handler
│   │   ├── routes.py         # /api/health, /api/wind/day
│   │   ├── service.py        # builds the full analysis for one date
│   │   ├── elexon.py         # HTTP client for the two datasets + small cache
│   │   ├── processing.py     # cleaning / de-duplication (pandas)
│   │   ├── selection.py      # cutoff, delivery periods, latest eligible forecast
│   │   ├── metrics.py        # error, MAE, RMSE, MAPE, shortfall
│   │   └── config.py         # environment-driven settings
│   ├── scripts/check_elexon.py   # run against the live API to confirm assumptions
│   └── tests/                # pytest; synthetic.py holds the fake test fixtures
└── frontend/
    ├── Dockerfile
    ├── package.json, vite.config.js, index.html, .env.example
    └── src/
        ├── main.jsx, App.jsx, api.js, format.js, styles.css
        └── components/       # GenerationChart, ErrorChart, AccuracySection,
                              # ProcurementSection, LargeErrorTable, MetricCard
```

## 10. Prerequisites

Docker Desktop (for the Docker route), or Python 3.12+ and Node 20+ (for the manual route). Internet access to `data.elexon.co.uk`.

## 11–12. Run with Docker

```bash
git clone <your-repo-url> windpulse && cd windpulse
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (health: http://localhost:8000/api/health, docs: http://localhost:8000/docs)

Stop with `Ctrl+C`, then `docker compose down`.

> The Docker setup was **not** built or run in the environment where this project was written (no Docker daemon was available); only the compose file syntax was validated. If a build fails, please fix and note it.

### Without Docker

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev                                           # http://localhost:5173
```

## 13. Environment variables

| Variable | Where | Default | Purpose |
| --- | --- | --- | --- |
| `VITE_API_URL` | frontend (build time) | `http://localhost:8000` | Backend base URL |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed browser origins |
| `DAY_AHEAD_CUTOFF` | backend | `09:20` | Cutoff, UK local time on the previous day |
| `ELEXON_BASE_URL` | backend | `https://data.elexon.co.uk/bmrs/api/v1` | Elexon API base |
| `ELEXON_TIMEOUT_SECONDS` | backend | `30` | Per-request timeout |
| `CACHE_TTL_SECONDS` | backend | `3600` | In-memory cache lifetime |
| `FORECAST_LOOKBACK_HOURS` | backend | `72` | How far before the cutoff to fetch publications |
| `MIN_MATCHED_PERIODS` | backend | `12` | Minimum matched half-hours to show metrics |

No secrets are needed; no API key is used. `.env` files are git-ignored.

## 14. Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

The tests use small synthetic fixtures (clearly labelled in `tests/synthetic.py`) and cover: timestamp matching, latest-eligible-forecast selection, exclusion of post-cutoff forecasts (and inclusion at exactly the cutoff), UK clock-change handling, MAE/RMSE, MAPE with zero actuals, missing/duplicate records, withheld metrics on thin coverage, invalid or out-of-range dates, and the HTTP client's parameters, caching and error mapping (with `requests.get` faked). They do not call Elexon.

Frontend build check: `cd frontend && npm run build`.

### Verifying the Elexon integration

From a machine that can reach Elexon:

```bash
cd backend
python -m scripts.check_elexon 2026-01-10
```

It prints each dataset's real field names, row counts, `publishTime` behaviour, time resolution, lead times and generation range. Compare with section 5 and fix `app/elexon.py` / `app/config.py` if anything differs.

## 15. Deployment

**Backend → Render**

1. Push the repo to GitHub, then in Render choose *New → Blueprint* (uses `render.yaml`) or *New → Web Service* with root directory `backend`.
2. Build command: `pip install -r requirements.txt` · Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` · Health check path: `/api/health`.
3. Set `CORS_ORIGINS` to your Vercel URL (e.g. `https://your-app.vercel.app`, no trailing slash).
4. After deploy, open `https://<service>.onrender.com/api/health`, then `/api/wind/day?date=2026-01-10`. This also confirms Render can reach Elexon.

**Frontend → Vercel**

1. Import the repo; set *Root Directory* to `frontend` (framework: Vite, build `npm run build`, output `dist`).
2. Add environment variable `VITE_API_URL` = your Render URL, then deploy. Redeploy after changing it.

## 16–17. Links

- Deployed application: **not deployed yet** (deployment needs your Render and Vercel accounts).
- GitHub repository: **not created yet** — use a random, non-identifying repository name.

## 18. Known limitations and possible future work

See section 8. Possible future work (not implemented): multi-day accuracy summaries, comparison of several cutoff times, a shared/persistent cache, a frontend test suite.

## 19. AI assistance disclosure

This project was designed and written with AI assistance: the code, tests and this documentation were generated by **Claude (Claude Sonnet 5.5, Anthropic)** working in an agentic coding environment, from a specification supplied by the project owner. The generated code was run through the automated checks described above, but it has not been verified against live Elexon data. The owner should read and understand the code before presenting it, and update this section if other AI tools were also used.

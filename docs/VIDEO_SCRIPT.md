# WindPulse demo video: script and checklist

Single YouTube video, **10 minutes maximum**: Part 1 (client, ≤5:00) then Part 2 (technical, ≤5:00). This is a script only; nothing has been recorded or uploaded.

Fill every `[...]` from the **real deployed app** while recording. Do not quote numbers you have not seen on screen.

## Before recording

- [ ] Backend and frontend deployed and working; `/api/health` returns ok.
- [ ] Run `python -m scripts.check_elexon 2026-01-10` and confirm units, WINDFOR resolution and parameter names. Fix anything that differs.
- [ ] Confirm the decision cutoff time you will state (default 09:20) and set `DAY_AHEAD_CUTOFF` to match.
- [ ] Pick two demo dates: one with good coverage, one with large errors. Note what the dashboard shows for each.
- [ ] Repo open in the editor, tests runnable (`python -m pytest`), browser at the deployed URL.
- [ ] Add the video link to the README when uploaded.

## Part 1: client presentation (target 4:30)

**0:00 – Problem (0:40).** "You buy power for tomorrow on the day-ahead market, before you know how much wind there will be. Wind is a large, variable share of GB supply, so the wind forecast you can see at decision time shapes how exposed you are. Two questions: what did the forecast say, and how reliable has that kind of forecast been?"

**0:40 – Dashboard tour (1:30).** Open the deployed app. Pick `[date]`. Point out the title, date picker (January 2026), summary cards (forecast vs actual average and peak, in MW), and the chart: dashed blue forecast, solid dark actual. "Forecast is what was predicted; actual is what the grid recorded."

**2:10 – Decision-time forecast (0:50).** Point to the forecast-basis banner. "For each half-hour we use the latest forecast published before `[cutoff]` the day before, not today's forecast, which a buyer couldn't have seen. Publish time used here: `[time]`."

**3:00 – Accuracy (1:00).** MAE `[x] MW`: typical miss. RMSE `[x] MW`: weights big misses. MAPE `[x]%`, excluding zero-output half-hours. Average error `[x] MW`: tendency to over- or under-forecast. Show the error chart and the large-error table. "These are the periods where the forecast was least dependable."

**4:00 – Limits and close (0:30).** "This does not include your demand, market prices or other generation, so it can't tell you how much to buy or what it costs. It shows how much to trust the wind forecast, to support your own judgment."

## Part 2: technical review (target 4:30)

**5:00 – Architecture (0:40).** React + Vite + Recharts on Vercel; FastAPI + pandas on Render; one endpoint `/api/wind/day`. Show the diagram in the README.

**5:40 – Data flow and selection (1:30).** Open `elexon.py` (FUELHH and WINDFOR streams, timeout, small cache), `processing.py` (cleaning, duplicates), then `selection.py`: `decision_cutoff` (UK local time → UTC, DST-safe) and `select_latest_forecasts` (`publish_time <= cutoff`, latest per `start_time`). Stress that a late forecast leaves a gap rather than being substituted.

**7:10 – Matching and metrics (0:50).** `service.py`: left-join on the expected 30-minute periods, matched mask, minimum-coverage rule. `metrics.py`: error = forecast − actual, MAE/RMSE/MAPE, zero-actual exclusion.

**8:00 – Tests (0:50).** Run `python -m pytest`; show `test_selection.py` (post-cutoff exclusion, exactly-at-cutoff) and the MAPE zero-actual test. Say plainly that tests use synthetic fixtures and do not hit Elexon.

**8:50 – Deployment, decisions, limitations (1:00).** Dockerfiles + compose, `render.yaml`, `VITE_API_URL` and `CORS_ORIGINS`. Be upfront: cutoff time is a configurable assumption with two disagreeing sources; units and parameter names were confirmed with `check_elexon` on `[date]` (state what you actually found); in-memory cache; AI assistance disclosed in the README.

**9:50 – Stop.**

## Recording checklist

- [ ] Total length under 10:00; Part 1 under 5:00 and Part 2 under 5:00.
- [ ] Two parts clearly announced on screen/voice.
- [ ] Deployed URL (not localhost) shown in Part 1.
- [ ] No secrets or personal data visible; random repository name.
- [ ] Uploaded to YouTube; link added to the README.

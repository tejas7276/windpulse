import { useEffect, useState } from "react";
import { fetchDay } from "./api";
import { formatMw, formatUkTime } from "./format";
import AccuracySection from "./components/AccuracySection";
import GenerationChart from "./components/GenerationChart";
import MetricCard from "./components/MetricCard";
import ProcurementSection from "./components/ProcurementSection";

// Keep in step with ANALYSIS_START / ANALYSIS_END in backend/app/config.py.
const MIN_DATE = "2026-01-01";
const MAX_DATE = "2026-01-31";

function ForecastBasis({ data }) {
  const { earliest, latest } = data.forecast_published_at;
  let published = "No forecast was available before the cutoff";
  if (latest) {
    published = earliest === latest ? formatUkTime(latest) : `${formatUkTime(earliest)} to ${formatUkTime(latest)}`;
  }
  return (
    <div className="notice" aria-label="Forecast basis">
      <strong>Forecast basis.</strong> For each half-hour we use the latest WINDFOR forecast published on or before{" "}
      <strong>{data.decision_cutoff_local}</strong> on the previous day. Forecast publish time used: {published}.
    </div>
  );
}

function Dashboard({ data }) {
  const hasForecast = data.coverage.forecast_periods > 0;
  const hasActual = data.coverage.actual_periods > 0;
  const { summary } = data;

  return (
    <>
      <ForecastBasis data={data} />

      <section>
        <h2>Wind generation on {data.date}</h2>
        <div className="cards">
          <MetricCard
            label="Forecast, average"
            value={formatMw(summary.forecast_mean_mw)}
            note={hasForecast ? `Peak ${formatMw(summary.forecast_peak_mw)}` : "No forecast for this day"}
          />
          <MetricCard
            label="Actual, average"
            value={formatMw(summary.actual_mean_mw)}
            note={hasActual ? `Peak ${formatMw(summary.actual_peak_mw)}` : "Actual data not available"}
          />
        </div>
        <GenerationChart points={data.points} />
        <p className="muted small">
          Half-hourly national wind generation in {data.unit}, shown in UK local time. Gaps in a line mean that series
          has no value for that half-hour.
        </p>
      </section>

      <AccuracySection data={data} />
      <ProcurementSection shortfall={data.shortfall} hasMatches={data.coverage.matched_periods > 0} />
    </>
  );
}

export default function App() {
  const [date, setDate] = useState(MIN_DATE);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!date) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetchDay(date, controller.signal)
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setData(null);
        setError(err.message);
        setLoading(false);
      });

    return () => controller.abort();
  }, [date, attempt]);

  const isEmpty = data && data.coverage.forecast_periods === 0 && data.coverage.actual_periods === 0;

  return (
    <main>
      <header>
        <h1>WindPulse</h1>
        <p className="subtitle">UK wind generation: day-ahead forecast vs actual, January 2026</p>
        <p className="muted small">
          National wind generation from Elexon (WINDFOR forecasts and FUELHH outturn).
        </p>
      </header>

      <div className="controls">
        <label htmlFor="date">Delivery date</label>
        <input
          id="date"
          type="date"
          value={date}
          min={MIN_DATE}
          max={MAX_DATE}
          onChange={(event) => event.target.value && setDate(event.target.value)}
        />
      </div>

      <div aria-live="polite">
        {loading && <p className="status">Loading data from Elexon…</p>}
      </div>

      {error && (
        <div className="error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => setAttempt((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {!loading && isEmpty && (
        <p className="status">No forecast or actual wind data was returned for {data.date}.</p>
      )}
      {!loading && data && !isEmpty && <Dashboard data={data} />}
    </main>
  );
}

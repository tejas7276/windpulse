import { formatMw, formatPercent, formatSignedMw } from "../format";
import ErrorChart from "./ErrorChart";
import LargeErrorTable from "./LargeErrorTable";
import MetricCard from "./MetricCard";

export default function AccuracySection({ data }) {
  const { metrics, metrics_note: note, coverage, points } = data;

  return (
    <section>
      <h2>Forecast accuracy</h2>
      <p className="muted">
        Evaluated on {data.date} (UK time), {coverage.matched_periods} of {coverage.expected_periods} half-hours
        had both a forecast and an actual value. Forecast error = forecast − actual, in MW.
      </p>

      {metrics ? (
        <>
          <div className="cards">
            <MetricCard label="MAE" value={formatMw(metrics.mae_mw)} note="Mean absolute error" />
            <MetricCard label="RMSE" value={formatMw(metrics.rmse_mw)} note="Penalises large misses more" />
            <MetricCard
              label="MAPE"
              value={formatPercent(metrics.mape_percent)}
              note={`Based on ${metrics.mape_observations} half-hours with non-zero actual output`}
            />
            <MetricCard
              label="Average error (bias)"
              value={formatSignedMw(metrics.mean_error_mw)}
              note="Positive = forecast tended to be too high"
            />
            <MetricCard
              label="Over-forecast"
              value={`${metrics.overforecast_periods} half-hours`}
              note={`Average ${formatSignedMw(metrics.mean_overforecast_mw)}`}
            />
            <MetricCard
              label="Under-forecast"
              value={`${metrics.underforecast_periods} half-hours`}
              note={`Average ${formatSignedMw(metrics.mean_underforecast_mw)}`}
            />
          </div>

          <details>
            <summary>How these are calculated</summary>
            <ul>
              <li>
                <strong>MAE</strong>: average of |forecast − actual| over matched half-hours.
              </li>
              <li>
                <strong>RMSE</strong>: square root of the average of (forecast − actual)².
              </li>
              <li>
                <strong>MAPE</strong>: average of |forecast − actual| ÷ actual, as a percentage. Half-hours where
                actual output is zero are left out because the ratio is undefined.
              </li>
            </ul>
          </details>
        </>
      ) : (
        <p className="notice">{note}</p>
      )}

      {coverage.matched_periods > 0 && (
        <>
          <h3>Forecast error by half-hour</h3>
          <ErrorChart points={points} />
          <LargeErrorTable points={points} threshold={data.large_error_threshold_mw} />
        </>
      )}

      <p className="muted small">
        Not matched: {coverage.unmatched_periods} half-hours ({coverage.expected_periods - coverage.forecast_periods}{" "}
        without a usable forecast, {coverage.expected_periods - coverage.actual_periods} without an actual).
      </p>
    </section>
  );
}

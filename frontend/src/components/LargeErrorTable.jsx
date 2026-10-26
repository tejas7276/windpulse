import { formatMw, formatSignedMw } from "../format";

export default function LargeErrorTable({ points, threshold }) {
  const flagged = points.filter((p) => p.large_error);

  if (threshold == null) return null;
  if (flagged.length === 0) {
    return <p className="muted">No half-hours exceeded the large-error threshold of {formatMw(threshold)}.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <caption>
          Half-hours where |error| exceeded {formatMw(threshold)} (1.5 × the day's MAE)
        </caption>
        <thead>
          <tr>
            <th scope="col">Time (UK)</th>
            <th scope="col">Forecast</th>
            <th scope="col">Actual</th>
            <th scope="col">Error (forecast − actual)</th>
          </tr>
        </thead>
        <tbody>
          {flagged.map((p) => (
            <tr key={p.start_time}>
              <td>{p.local_time}</td>
              <td>{formatMw(p.forecast_mw)}</td>
              <td>{formatMw(p.actual_mw)}</td>
              <td>{formatSignedMw(p.error_mw)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

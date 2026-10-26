import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatSignedMw } from "../format";

const OVER = "#d97706";
const UNDER = "#0e7490";

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  const direction = point.error_mw > 0 ? "over-forecast" : point.error_mw < 0 ? "under-forecast" : "exact";
  return (
    <div className="tooltip">
      <strong>{label} (UK time)</strong>
      <div>Error: {formatSignedMw(point.error_mw)} ({direction})</div>
      {point.large_error && <div>Flagged as a large error</div>}
    </div>
  );
}

export default function ErrorChart({ points }) {
  return (
    <div className="chart" role="img" aria-label="Forecast error per half-hour in megawatts, forecast minus actual">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="local_time" interval={3} tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => v.toLocaleString("en-GB")}
            label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }}
          />
          <Tooltip content={<ChartTooltip />} />
          <ReferenceLine y={0} stroke="#6b7280" />
          <Bar dataKey="error_mw" name="Forecast error">
            {points.map((point) => (
              <Cell
                key={point.start_time}
                fill={point.error_mw > 0 ? OVER : UNDER}
                fillOpacity={point.large_error ? 1 : 0.45}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="legend-note">
        <span className="swatch" style={{ background: OVER }} /> over-forecast (above zero)
        <span className="swatch" style={{ background: UNDER }} /> under-forecast (below zero)
        · Solid bars are large errors.
      </p>
    </div>
  );
}

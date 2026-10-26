import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatMw } from "../format";

export const COLORS = { forecast: "#2563eb", actual: "#111827" };

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="tooltip">
      <strong>{label} (UK time)</strong>
      <div style={{ color: COLORS.forecast }}>Forecast: {formatMw(point.forecast_mw)}</div>
      <div style={{ color: COLORS.actual }}>Actual: {formatMw(point.actual_mw)}</div>
    </div>
  );
}

export default function GenerationChart({ points }) {
  return (
    <div className="chart" role="img" aria-label="Half-hourly forecast and actual wind generation in megawatts">
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="local_time" interval={3} tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => v.toLocaleString("en-GB")}
            label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="forecast_mw"
            name="Forecast (WINDFOR)"
            stroke={COLORS.forecast}
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="actual_mw"
            name="Actual (FUELHH)"
            stroke={COLORS.actual}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

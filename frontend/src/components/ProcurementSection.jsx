import { formatMw, formatMwh } from "../format";
import MetricCard from "./MetricCard";

export default function ProcurementSection({ shortfall, hasMatches }) {
  return (
    <section>
      <h2>What this means for day-ahead buying</h2>

      {hasMatches ? (
        <>
          <div className="cards">
            <MetricCard
              label="Half-hours with a shortfall"
              value={shortfall.periods}
              note="Actual wind output was above the forecast"
            />
            <MetricCard label="Largest shortfall" value={formatMw(shortfall.max_mw)} note="Peak of actual − forecast" />
            <MetricCard
              label="Total shortfall"
              value={formatMwh(shortfall.energy_mwh)}
              note="Sum of half-hourly MW × 0.5 h"
            />
          </div>
          <p className="muted small">
            Shortfall = max(actual − forecast, 0), as defined in the project brief. It is positive only when the
            forecast <em>under</em>-estimated wind output; half-hours where the forecast was too high count as zero.
          </p>
        </>
      ) : (
        <p className="muted">Shortfall figures need half-hours with both a forecast and an actual value.</p>
      )}

      <div className="notice">
        <strong>Read this as a descriptive comparison only.</strong> WindPulse has no data on consumer demand, market
        prices, dispatch or other generation sources, so it cannot work out how much power you need to buy or what it
        would cost. It shows how far national wind output differed from the forecast that was available at the
        day-ahead decision time.
      </div>
    </section>
  );
}

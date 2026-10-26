const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

export const MISSING = "–";

export function formatMw(value) {
  return value == null ? MISSING : `${number.format(value)} MW`;
}

export function formatSignedMw(value) {
  if (value == null) return MISSING;
  const sign = value > 0 ? "+" : "";
  return `${sign}${number.format(value)} MW`;
}

export function formatPercent(value) {
  return value == null ? MISSING : `${value.toFixed(1)}%`;
}

export function formatMwh(value) {
  return value == null ? MISSING : `${number.format(value)} MWh`;
}

// ISO timestamp -> UK local date and time, e.g. "9 Jan 2026, 08:00 GMT"
export function formatUkTime(iso) {
  if (!iso) return MISSING;
  return new Date(iso).toLocaleString("en-GB", {
    timeZone: "Europe/London",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

export default function MetricCard({ label, value, note }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
      {note && <div className="card-note">{note}</div>}
    </div>
  );
}

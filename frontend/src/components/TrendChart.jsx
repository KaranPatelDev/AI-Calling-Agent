import { useState } from "react";

const SERIES = [
  { key: "completed", label: "Completed", color: "var(--chart-series-good)" },
  { key: "no_answer", label: "No answer", color: "var(--chart-series-warn)" },
  { key: "failed", label: "Not placed", color: "var(--chart-series-bad)" },
];

function bucketByDay(calls, days) {
  const buckets = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    buckets.push({
      key,
      label: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      completed: 0,
      no_answer: 0,
      failed: 0,
    });
  }
  const byKey = Object.fromEntries(buckets.map((b) => [b.key, b]));
  calls.forEach((c) => {
    const key = new Date(c.scheduled_at).toISOString().slice(0, 10);
    const bucket = byKey[key];
    if (bucket && (c.status === "completed" || c.status === "no_answer" || c.status === "failed")) {
      bucket[c.status] += 1;
    }
  });
  return buckets;
}

export default function TrendChart({ calls }) {
  const [range, setRange] = useState(7);
  const [hovered, setHovered] = useState(null);
  const buckets = bucketByDay(calls, range);
  const max = Math.max(1, ...buckets.map((b) => b.completed + b.no_answer + b.failed));

  return (
    <div className="viz-root chart-card">
      <div className="chart-header">
        <div className="chart-title">Calls over time</div>
        <div className="row">
          <button
            type="button"
            className={range === 7 ? "btn-audience active" : "btn-audience"}
            onClick={() => setRange(7)}
          >
            7d
          </button>
          <button
            type="button"
            className={range === 30 ? "btn-audience active" : "btn-audience"}
            onClick={() => setRange(30)}
          >
            30d
          </button>
        </div>
      </div>
      <div className="trend-chart">
        {buckets.map((b) => {
          const total = b.completed + b.no_answer + b.failed;
          return (
            <div
              className="trend-bar-group"
              key={b.key}
              onMouseEnter={() => setHovered(b.key)}
              onMouseLeave={() => setHovered(null)}
            >
              <div className="trend-bar-stack">
                {SERIES.map((s) => {
                  const value = b[s.key];
                  const heightPct = (value / max) * 100;
                  return value > 0 ? (
                    <div key={s.key} className="trend-bar-segment" style={{ height: `${heightPct}%`, background: s.color }} />
                  ) : null;
                })}
              </div>
              {range === 7 && <span className="trend-bar-label">{b.label}</span>}
              {hovered === b.key && (
                <div className="chart-tooltip trend-tooltip">
                  <strong>{b.label}</strong>
                  {total === 0 ? (
                    <div>No calls</div>
                  ) : (
                    SERIES.map((s) => (
                      <div key={s.key}>
                        {s.label}: {b[s.key]}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="chart-legend">
        {SERIES.map((s) => (
          <span className="chart-legend-item" key={s.key}>
            <span className="chart-legend-swatch" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

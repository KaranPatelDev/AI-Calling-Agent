import { useState } from "react";

const SERIES = [
  { key: "buyer", label: "Buyers", color: "var(--chart-series-1)" },
  { key: "seller", label: "Sellers", color: "var(--chart-series-2)" },
];

export default function BuyerSellerChart({ calls }) {
  const [hovered, setHovered] = useState(null);
  const counts = {
    buyer: calls.filter((c) => c.audience === "buyer").length,
    seller: calls.filter((c) => c.audience === "seller").length,
  };
  const max = Math.max(counts.buyer, counts.seller, 1);

  return (
    <div className="viz-root chart-card">
      <div className="chart-title">Calls by audience</div>
      <div className="bar-row-chart">
        {SERIES.map((s) => {
          const value = counts[s.key];
          const pct = (value / max) * 100;
          return (
            <div
              className="bar-row"
              key={s.key}
              onMouseEnter={() => setHovered(s.key)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="bar-row-label">{s.label}</span>
              <div className="bar-row-track">
                <div className="bar-row-fill" style={{ width: `${pct}%`, background: s.color }} />
              </div>
              <span className="bar-row-value">{value}</span>
              {hovered === s.key && (
                <div className="chart-tooltip">
                  {s.label}: {value} call{value === 1 ? "" : "s"}
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

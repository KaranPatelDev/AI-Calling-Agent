import { useEffect, useState } from "react";

import { api } from "../api.js";
import AudienceTabs from "../components/AudienceTabs.jsx";

const STATS = [
  { key: "total", label: "Total calls" },
  { key: "completed", label: "Completed" },
  { key: "failed", label: "Failed" },
  { key: "scheduled", label: "Scheduled" },
];

function computeStats(calls) {
  return {
    total: calls.length,
    completed: calls.filter((c) => c.status === "completed").length,
    failed: calls.filter((c) => c.status === "failed").length,
    scheduled: calls.filter((c) => c.status === "scheduled" || c.status === "pending").length,
  };
}

export default function Dashboard() {
  const [calls, setCalls] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  async function refresh() {
    try {
      setCalls(await api.listCalls());
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10000);
    return () => clearInterval(id);
  }, []);

  const filtered = filter === "all" ? calls : calls.filter((c) => c.audience === filter);
  const stats = computeStats(filtered);

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of every call placed or scheduled.</p>
        </div>
        <button type="button" className="btn-secondary" onClick={refresh}>
          Refresh
        </button>
      </div>

      <AudienceTabs value={filter} onChange={setFilter} />

      <div className="stat-grid">
        {STATS.map((s) => (
          <div className="stat-card" key={s.key}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value">{stats[s.key]}</div>
          </div>
        ))}
      </div>

      {error && <p className="status">{error}</p>}

      <div className="table-card">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">No calls yet — place one from New Call.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Organization</th>
                <th>Audience</th>
                <th>Phone</th>
                <th>Scheduled</th>
                <th>Status</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>{c.recipient_name}</td>
                  <td>{c.organization || "—"}</td>
                  <td>
                    <span className="audience-tag">{c.audience}</span>
                  </td>
                  <td>{c.phone_number}</td>
                  <td>{new Date(c.scheduled_at).toLocaleString()}</td>
                  <td>
                    <span className={`badge badge-${c.status}`}>{c.status}</span>
                  </td>
                  <td>{c.error_message || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

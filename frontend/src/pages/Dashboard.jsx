import { useEffect, useState } from "react";

import { api } from "../api.js";
import Tabs from "../components/Tabs.jsx";

const STATS = [
  { key: "total", label: "Total calls" },
  { key: "completed", label: "Completed" },
  { key: "no_answer", label: "No answer" },
  { key: "failed", label: "Not placed" },
  { key: "scheduled", label: "Scheduled" },
];

const AUDIENCE_OPTIONS = [
  { value: "all", label: "All" },
  { value: "buyer", label: "Buyers" },
  { value: "seller", label: "Sellers" },
];

const OUTCOME_OPTIONS = [
  { value: "all", label: "All outcomes" },
  { value: "completed", label: "Successful" },
  { value: "failed", label: "Not placed" },
  { value: "no_answer", label: "No answer" },
];

function computeStats(calls) {
  return {
    total: calls.length,
    completed: calls.filter((c) => c.status === "completed").length,
    no_answer: calls.filter((c) => c.status === "no_answer").length,
    failed: calls.filter((c) => c.status === "failed").length,
    scheduled: calls.filter((c) => c.status === "scheduled" || c.status === "pending").length,
  };
}

export default function Dashboard() {
  const [calls, setCalls] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [audienceFilter, setAudienceFilter] = useState("all");
  const [outcomeFilter, setOutcomeFilter] = useState("all");

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

  async function handleDelete(id) {
    try {
      await api.cancelCall(id);
      refresh();
    } catch (err) {
      setError(`Delete failed: ${err.message}`);
    }
  }

  async function handleClearHistory() {
    if (!window.confirm("Permanently delete all completed, failed, no-answer, and cancelled calls from history?")) {
      return;
    }
    try {
      await api.clearCallHistory();
      refresh();
    } catch (err) {
      setError(`Clear history failed: ${err.message}`);
    }
  }

  const filtered = calls
    .filter((c) => audienceFilter === "all" || c.audience === audienceFilter)
    .filter((c) => outcomeFilter === "all" || c.status === outcomeFilter);
  const stats = computeStats(filtered);

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of every call placed or scheduled.</p>
        </div>
        <div className="row">
          <button type="button" className="btn-ghost" onClick={handleClearHistory}>
            Clear history
          </button>
          <button type="button" className="btn-secondary" onClick={refresh}>
            Refresh
          </button>
        </div>
      </div>

      <Tabs options={AUDIENCE_OPTIONS} value={audienceFilter} onChange={setAudienceFilter} />
      <Tabs options={OUTCOME_OPTIONS} value={outcomeFilter} onChange={setOutcomeFilter} />

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
          <div className="empty-state">No calls match this filter.</div>
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
                <th></th>
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
                    <span className={`badge badge-${c.status}`}>{c.status.replace("_", " ")}</span>
                  </td>
                  <td>{c.error_message || "—"}</td>
                  <td>
                    <button type="button" className="btn-danger btn-sm" onClick={() => handleDelete(c.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

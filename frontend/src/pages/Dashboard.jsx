import { useEffect, useState } from "react";

import { api } from "../api.js";
import BuyerSellerChart from "../components/BuyerSellerChart.jsx";
import Tabs from "../components/Tabs.jsx";
import TrendChart from "../components/TrendChart.jsx";

const STATS = [
  { key: "total", label: "Total calls" },
  { key: "completed", label: "Completed" },
  { key: "no_answer", label: "No answer" },
  { key: "cut_off", label: "Cut off" },
  { key: "voicemail", label: "Voicemail" },
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
  { value: "cut_off", label: "Cut off" },
  { value: "voicemail", label: "Voicemail" },
  { value: "scheduled", label: "Scheduled" },
];

function matchesOutcome(call, outcomeFilter) {
  if (outcomeFilter === "all") return true;
  if (outcomeFilter === "scheduled") return call.status === "scheduled" || call.status === "pending";
  return call.status === outcomeFilter;
}

function computeStats(calls) {
  const completed = calls.filter((c) => c.status === "completed").length;
  const no_answer = calls.filter((c) => c.status === "no_answer").length;
  const cut_off = calls.filter((c) => c.status === "cut_off").length;
  const voicemail = calls.filter((c) => c.status === "voicemail").length;
  const failed = calls.filter((c) => c.status === "failed").length;
  const attempted = completed + no_answer + cut_off + voicemail + failed;
  const pct = (n) => (attempted === 0 ? 0 : Math.round((n / attempted) * 100));
  return {
    total: calls.length,
    completed,
    no_answer,
    cut_off,
    voicemail,
    failed,
    scheduled: calls.filter((c) => c.status === "scheduled" || c.status === "pending").length,
    attempted,
    completedPct: pct(completed),
    noAnswerPct: pct(no_answer),
    failedPct: pct(failed),
  };
}

export default function Dashboard() {
  const [calls, setCalls] = useState([]);
  const [inboundCalls, setInboundCalls] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [audienceFilter, setAudienceFilter] = useState("all");
  const [outcomeFilter, setOutcomeFilter] = useState("all");

  async function refresh() {
    try {
      const [callsData, inboundData] = await Promise.all([api.listCalls(), api.listInboundCalls()]);
      setCalls(callsData);
      setInboundCalls(inboundData);
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
    .filter((c) => matchesOutcome(c, outcomeFilter));
  const stats = computeStats(filtered);
  const interestRate = stats.attempted === 0 ? 0 : Math.round((inboundCalls.length / stats.attempted) * 100);

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
            {s.key === "completed" && <div className="stat-sublabel">{stats.completedPct}% of attempted calls</div>}
            {s.key === "no_answer" && <div className="stat-sublabel">{stats.noAnswerPct}% of attempted calls</div>}
            {s.key === "failed" && <div className="stat-sublabel">{stats.failedPct}% of attempted calls</div>}
          </div>
        ))}
      </div>

      <div className="charts-grid">
        <BuyerSellerChart calls={filtered} />
        <TrendChart calls={filtered} />
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

      <div className="topbar">
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Inbound interest</h1>
          <p>People who called your Plivo number back — a sign they're genuinely interested.</p>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total callbacks</div>
          <div className="stat-value">{inboundCalls.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Interest rate</div>
          <div className="stat-value">{interestRate}%</div>
          <div className="stat-sublabel">callbacks ÷ attempted calls</div>
        </div>
      </div>

      <div className="table-card">
        {inboundCalls.length === 0 ? (
          <div className="empty-state">No callbacks yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Caller</th>
                <th>Phone</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Callback</th>
              </tr>
            </thead>
            <tbody>
              {inboundCalls.map((c) => (
                <tr key={c.id}>
                  <td>
                    {c.matched_name || "Unknown caller"}
                    {c.matched_organization ? ` (${c.matched_organization})` : ""}
                  </td>
                  <td>{c.from_number}</td>
                  <td>{new Date(c.created_at).toLocaleString()}</td>
                  <td>{c.duration_seconds != null ? `${c.duration_seconds}s` : "—"}</td>
                  <td>
                    <span className={`badge badge-${c.status === "completed" ? "completed" : "scheduled"}`}>
                      {c.missed ? "missed" : c.status}
                    </span>
                  </td>
                  <td>
                    {c.auto_callback_scheduled_at ? (
                      <>
                        <span className={`badge badge-${c.auto_callback_status}`}>{c.auto_callback_status}</span>{" "}
                        {new Date(c.auto_callback_scheduled_at).toLocaleString()}
                      </>
                    ) : (
                      "—"
                    )}
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

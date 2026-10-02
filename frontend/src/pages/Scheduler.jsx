import { useEffect, useState } from "react";

import { api } from "../api.js";
import AudienceToggle from "../components/AudienceToggle.jsx";
import RecipientsEditor from "../components/RecipientsEditor.jsx";
import ScriptEditor from "../components/ScriptEditor.jsx";
import ScriptPicker from "../components/ScriptPicker.jsx";
import SpeedControl from "../components/SpeedControl.jsx";
import Tabs from "../components/Tabs.jsx";
import { useAudienceScript } from "../hooks/useAudienceScript.js";

const AUDIENCE_FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "buyer", label: "Buyers" },
  { value: "seller", label: "Sellers" },
];

function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function defaultScheduledAt() {
  return toLocalInputValue(new Date(Date.now() + 3600 * 1000));
}

export default function Scheduler() {
  const [recipients, setRecipients] = useState([{ name: "", phone: "", organization: "" }]);
  const [scriptText, setScriptText] = useState("");
  const { audience, setAudience } = useAudienceScript(setScriptText);
  const [speechRate, setSpeechRate] = useState("");
  const [scheduledAt, setScheduledAt] = useState(defaultScheduledAt());
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [upcoming, setUpcoming] = useState([]);
  const [loadingUpcoming, setLoadingUpcoming] = useState(true);
  const [upcomingFilter, setUpcomingFilter] = useState("all");

  // inline-edit state for rescheduling a retry call
  const [editingId, setEditingId] = useState(null);
  const [editingAt, setEditingAt] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  async function refreshUpcoming() {
    try {
      const calls = await api.listCalls();
      setUpcoming(
        calls
          .filter((c) => c.status === "scheduled")
          .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
      );
    } catch (err) {
      setStatus(`Failed to load upcoming calls: ${err.message}`);
    } finally {
      setLoadingUpcoming(false);
    }
  }

  useEffect(() => {
    refreshUpcoming();
    const id = setInterval(refreshUpcoming, 10000);
    return () => clearInterval(id);
  }, []);

  function quickSchedule(hoursFromNow) {
    setScheduledAt(toLocalInputValue(new Date(Date.now() + hoursFromNow * 3600 * 1000)));
  }

  async function submit(e) {
    e.preventDefault();
    const valid = recipients.filter((r) => r.name.trim() && r.phone.trim());
    if (!valid.length || !scriptText.trim() || !scheduledAt) {
      setStatus("Add at least one recipient, a script, and a time.");
      return;
    }
    setSubmitting(true);
    setStatus("Scheduling...");
    try {
      const created = await api.createCalls({
        recipients: valid,
        script_text: scriptText,
        audience,
        scheduled_at: new Date(scheduledAt).toISOString(),
        speech_rate: speechRate === "" ? null : Number(speechRate),
      });
      setStatus(`Scheduled ${created.length} call(s).`);
      setRecipients([{ name: "", phone: "", organization: "" }]);
      setScriptText("");
      setScheduledAt(defaultScheduledAt());
      refreshUpcoming();
    } catch (err) {
      setStatus(`Failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel(id) {
    try {
      await api.cancelCall(id);
      if (editingId === id) setEditingId(null);
      refreshUpcoming();
    } catch (err) {
      setStatus(`Cancel failed: ${err.message}`);
    }
  }

  function startEdit(call) {
    setEditingId(call.id);
    setEditingAt(toLocalInputValue(new Date(call.scheduled_at)));
  }

  function cancelEdit() {
    setEditingId(null);
    setEditingAt("");
  }

  async function saveEdit(id) {
    if (!editingAt) return;
    setEditSaving(true);
    try {
      await api.rescheduleCall(id, new Date(editingAt).toISOString());
      setEditingId(null);
      setEditingAt("");
      refreshUpcoming();
    } catch (err) {
      setStatus(`Reschedule failed: ${err.message}`);
    } finally {
      setEditSaving(false);
    }
  }

  const regularCalls = upcoming.filter((c) => !c.is_retry);
  const retryCalls = upcoming.filter((c) => c.is_retry);

  function applyFilter(list) {
    return upcomingFilter === "all" ? list : list.filter((c) => c.audience === upcomingFilter);
  }

  function CallRow({ c, showRetryBadge }) {
    const isEditing = editingId === c.id;
    return (
      <tr key={c.id}>
        <td>{c.recipient_name}</td>
        <td>{c.organization || "—"}</td>
        <td>
          <span className="audience-tag">{c.audience}</span>
          {showRetryBadge && (
            <span className="audience-tag" style={{ marginLeft: "0.35rem", background: "#fef3c7", color: "#92400e" }}>
              auto-retry
            </span>
          )}
        </td>
        <td>{c.phone_number}</td>
        <td>
          {isEditing ? (
            <div className="row" style={{ gap: "0.4rem", flexWrap: "wrap" }}>
              <input
                type="datetime-local"
                value={editingAt}
                onChange={(e) => setEditingAt(e.target.value)}
                style={{ fontSize: "0.85rem" }}
              />
              <button
                type="button"
                className="btn-sm"
                disabled={editSaving}
                onClick={() => saveEdit(c.id)}
              >
                {editSaving ? "Saving…" : "Save"}
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={cancelEdit}>
                Cancel
              </button>
            </div>
          ) : (
            new Date(c.scheduled_at).toLocaleString()
          )}
        </td>
        <td>
          <div className="row" style={{ gap: "0.4rem", justifyContent: "flex-end" }}>
            {!isEditing && (
              <button type="button" className="btn-secondary btn-sm" onClick={() => startEdit(c)}>
                Edit time
              </button>
            )}
            <button type="button" className="btn-danger btn-sm" onClick={() => handleCancel(c.id)}>
              Cancel
            </button>
          </div>
        </td>
      </tr>
    );
  }

  function CallTable({ calls, showRetryBadge, emptyText }) {
    const filtered = applyFilter(calls);
    if (filtered.length === 0) {
      return <div className="empty-state">{emptyText}</div>;
    }
    return (
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Organization</th>
            <th>Audience</th>
            <th>Phone</th>
            <th>Runs at</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((c) => (
            <CallRow key={c.id} c={c} showRetryBadge={showRetryBadge} />
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Call Scheduler</h1>
          <p>Queue calls for a future time — they fire automatically, even hours from now.</p>
        </div>
      </div>

      <form className="card form-card" onSubmit={submit}>
        <AudienceToggle value={audience} onChange={setAudience} />

        <RecipientsEditor recipients={recipients} setRecipients={setRecipients} />

        <ScriptPicker onChange={setScriptText} />

        <ScriptEditor value={scriptText} onChange={setScriptText} />

        <SpeedControl value={speechRate} onChange={setSpeechRate} />

        <div className="field-group">
          <label className="field-label">When</label>
          <div className="row">
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
            <button type="button" className="btn-secondary btn-sm" onClick={() => quickSchedule(1)}>
              +1h
            </button>
            <button type="button" className="btn-secondary btn-sm" onClick={() => quickSchedule(15)}>
              +15h
            </button>
            <button type="button" className="btn-secondary btn-sm" onClick={() => quickSchedule(24)}>
              +24h
            </button>
          </div>
        </div>

        <div className="row">
          <button type="submit" disabled={submitting}>
            {submitting ? "Scheduling…" : "Schedule call(s)"}
          </button>
          {status && <p className="status">{status}</p>}
        </div>
      </form>

      <div className="topbar" style={{ marginTop: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Upcoming scheduled calls</h1>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            Manually scheduled calls waiting to fire.
          </p>
        </div>
      </div>

      <Tabs options={AUDIENCE_FILTER_OPTIONS} value={upcomingFilter} onChange={setUpcomingFilter} />

      <div className="table-card">
        {loadingUpcoming ? (
          <div className="empty-state">Loading…</div>
        ) : (
          <CallTable calls={regularCalls} showRetryBadge={false} emptyText="Nothing scheduled right now." />
        )}
      </div>

      <div className="topbar" style={{ marginTop: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Auto-rescheduled calls</h1>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            Calls automatically queued 24 h later because the recipient didn't answer. You can
            edit the time or cancel any of these.
          </p>
        </div>
      </div>

      <div className="table-card">
        {loadingUpcoming ? (
          <div className="empty-state">Loading…</div>
        ) : (
          <CallTable calls={retryCalls} showRetryBadge emptyText="No auto-rescheduled calls." />
        )}
      </div>
    </div>
  );
}

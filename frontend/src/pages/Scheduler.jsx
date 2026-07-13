import { useEffect, useState } from "react";

import { api } from "../api.js";
import AudienceTabs from "../components/AudienceTabs.jsx";
import AudienceToggle from "../components/AudienceToggle.jsx";
import RecipientsEditor from "../components/RecipientsEditor.jsx";
import ScriptEditor from "../components/ScriptEditor.jsx";
import { useAudienceScript } from "../hooks/useAudienceScript.js";

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
  const [scheduledAt, setScheduledAt] = useState(defaultScheduledAt());
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [upcoming, setUpcoming] = useState([]);
  const [loadingUpcoming, setLoadingUpcoming] = useState(true);
  const [upcomingFilter, setUpcomingFilter] = useState("all");

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
      refreshUpcoming();
    } catch (err) {
      setStatus(`Cancel failed: ${err.message}`);
    }
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

        <ScriptEditor value={scriptText} onChange={setScriptText} />

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

      <div className="topbar">
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Upcoming scheduled calls</h1>
        </div>
      </div>

      <AudienceTabs value={upcomingFilter} onChange={setUpcomingFilter} />

      <div className="table-card">
        {loadingUpcoming ? (
          <div className="empty-state">Loading…</div>
        ) : (
          (() => {
            const filtered =
              upcomingFilter === "all" ? upcoming : upcoming.filter((c) => c.audience === upcomingFilter);
            return filtered.length === 0 ? (
              <div className="empty-state">Nothing scheduled right now.</div>
            ) : (
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
                    <tr key={c.id}>
                      <td>{c.recipient_name}</td>
                      <td>{c.organization || "—"}</td>
                      <td>
                        <span className="audience-tag">{c.audience}</span>
                      </td>
                      <td>{c.phone_number}</td>
                      <td>{new Date(c.scheduled_at).toLocaleString()}</td>
                      <td>
                        <button type="button" className="btn-danger btn-sm" onClick={() => handleCancel(c.id)}>
                          Cancel
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            );
          })()
        )}
      </div>
    </div>
  );
}

import { useState } from "react";

import { api } from "../api.js";
import AudienceToggle from "../components/AudienceToggle.jsx";
import RecipientsEditor from "../components/RecipientsEditor.jsx";
import ScriptEditor from "../components/ScriptEditor.jsx";
import { useAudienceScript } from "../hooks/useAudienceScript.js";

export default function NewCall() {
  const [recipients, setRecipients] = useState([{ name: "", phone: "", organization: "" }]);
  const [scriptText, setScriptText] = useState("");
  const { audience, setAudience } = useAudienceScript(setScriptText);
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(e) {
    e.preventDefault();
    const valid = recipients.filter((r) => r.name.trim() && r.phone.trim());
    if (!valid.length || !scriptText.trim()) {
      setStatus("Add at least one recipient and a script.");
      return;
    }
    setSubmitting(true);
    setStatus("Placing call(s)...");
    try {
      const created = await api.createCalls({ recipients: valid, script_text: scriptText, audience, scheduled_at: null });
      setStatus(`Placed ${created.length} call(s) — check the Dashboard for live status.`);
      setRecipients([{ name: "", phone: "", organization: "" }]);
      setScriptText("");
    } catch (err) {
      setStatus(`Failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>New Call</h1>
          <p>Upload or enter recipients, write a script, and call them right now.</p>
        </div>
      </div>

      <form className="card form-card" onSubmit={submit}>
        <AudienceToggle value={audience} onChange={setAudience} />

        <RecipientsEditor recipients={recipients} setRecipients={setRecipients} />

        <ScriptEditor value={scriptText} onChange={setScriptText} />

        <div className="row">
          <button type="submit" disabled={submitting}>
            {submitting ? "Placing…" : "Call now"}
          </button>
          {status && <p className="status">{status}</p>}
        </div>
      </form>
    </div>
  );
}

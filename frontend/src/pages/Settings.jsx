import { useEffect, useState } from "react";

import { api } from "../api.js";
import ScriptEditor from "../components/ScriptEditor.jsx";

export default function Settings() {
  const [buyerScript, setBuyerScript] = useState("");
  const [sellerScript, setSellerScript] = useState("");
  const [speechRate, setSpeechRate] = useState(50);
  const [autoCallbackEnabled, setAutoCallbackEnabled] = useState(true);
  const [missedCallbackScript, setMissedCallbackScript] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  const [scripts, setScripts] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [draftName, setDraftName] = useState("");
  const [draftText, setDraftText] = useState("");
  const [savingScript, setSavingScript] = useState(false);
  const [scriptStatus, setScriptStatus] = useState("");

  useEffect(() => {
    api
      .getScriptSettings()
      .then((s) => {
        setBuyerScript(s.buyer_script || "");
        setSellerScript(s.seller_script || "");
        setSpeechRate(s.speech_rate ?? 50);
        setAutoCallbackEnabled(s.auto_callback_enabled ?? true);
        setMissedCallbackScript(s.missed_callback_script || "");
      })
      .catch((err) => setStatus(`Failed to load: ${err.message}`))
      .finally(() => setLoading(false));
    refreshScripts();
  }, []);

  async function refreshScripts() {
    try {
      setScripts(await api.listScripts());
    } catch (err) {
      setScriptStatus(`Failed to load scripts: ${err.message}`);
    }
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setStatus("");
    try {
      await api.saveScriptSettings({
        buyer_script: buyerScript,
        seller_script: sellerScript,
        speech_rate: Number(speechRate),
        auto_callback_enabled: autoCallbackEnabled,
        missed_callback_script: missedCallbackScript,
      });
      setStatus("Saved.");
    } catch (err) {
      setStatus(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  function startNewScript() {
    setEditingId(null);
    setDraftName("");
    setDraftText("");
    setScriptStatus("");
  }

  function startEditScript(script) {
    setEditingId(script.id);
    setDraftName(script.name);
    setDraftText(script.script_text);
    setScriptStatus("");
  }

  async function saveScript(e) {
    e.preventDefault();
    if (!draftName.trim() || !draftText.trim()) {
      setScriptStatus("Give the script a name and some text.");
      return;
    }
    setSavingScript(true);
    setScriptStatus("");
    try {
      const payload = { name: draftName.trim(), script_text: draftText };
      if (editingId) {
        await api.updateScript(editingId, payload);
      } else {
        await api.createScript(payload);
      }
      startNewScript();
      refreshScripts();
    } catch (err) {
      setScriptStatus(`Save failed: ${err.message}`);
    } finally {
      setSavingScript(false);
    }
  }

  async function deleteScript(id) {
    if (!window.confirm("Delete this saved script?")) return;
    try {
      await api.deleteScript(id);
      if (editingId === id) startNewScript();
      refreshScripts();
    } catch (err) {
      setScriptStatus(`Delete failed: ${err.message}`);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="topbar">
          <h1>Settings</h1>
        </div>
        <div className="empty-state">Loading…</div>
      </div>
    );
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Settings</h1>
          <p>Save a default script for each audience — New Call and Scheduler auto-fill it when you pick Buyer or Seller.</p>
        </div>
      </div>

      <form className="card form-card" onSubmit={save}>
        <ScriptEditor value={buyerScript} onChange={setBuyerScript} label="Default script — Buyers" />
        <ScriptEditor value={sellerScript} onChange={setSellerScript} label="Default script — Sellers" />

        <div className="field-group">
          <label className="field-label">Speaking speed</label>
          <p className="field-hint">
            Percent of normal speed (lower = slower). Use "Slow down" in the script editor to slow just a phrase
            further.
          </p>
          <div className="row">
            <input
              type="number"
              min="40"
              max="120"
              value={speechRate}
              onChange={(e) => setSpeechRate(e.target.value)}
              style={{ width: "6rem" }}
            />
            <span>%</span>
          </div>
        </div>

        <div className="field-group">
          <label className="field-label">Automatic missed-callback retry</label>
          <p className="field-hint">
            If someone calls back and the forwarded number doesn't pick up, automatically call them back ~24 hours
            later (pushed to Monday if that lands on a Sunday) — no approval needed. Turn off anytime to stop new
            ones from being scheduled.
          </p>
          <label className="row" style={{ fontWeight: 500 }}>
            <input
              type="checkbox"
              checked={autoCallbackEnabled}
              onChange={(e) => setAutoCallbackEnabled(e.target.checked)}
              style={{ width: "auto" }}
            />
            Enable automatic missed-callback retry
          </label>
        </div>

        <ScriptEditor
          value={missedCallbackScript}
          onChange={setMissedCallbackScript}
          label="Missed-callback script (used automatically, no approval)"
        />

        <div className="row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
          {status && <p className="status">{status}</p>}
        </div>
      </form>

      <div className="topbar">
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Script library</h1>
          <p>Save as many named scripts as you want — pick any of them from a dropdown when placing a call.</p>
        </div>
      </div>

      <form className="card form-card" onSubmit={saveScript}>
        <div className="field-group">
          <label className="field-label">Script name</label>
          <input
            placeholder="e.g. Diwali offer follow-up"
            value={draftName}
            onChange={(e) => setDraftName(e.target.value)}
          />
        </div>

        <ScriptEditor value={draftText} onChange={setDraftText} label="Script text" />

        <div className="row">
          <button type="submit" disabled={savingScript}>
            {savingScript ? "Saving…" : editingId ? "Update script" : "Save as new script"}
          </button>
          {editingId && (
            <button type="button" className="btn-secondary" onClick={startNewScript}>
              Cancel edit
            </button>
          )}
          {scriptStatus && <p className="status">{scriptStatus}</p>}
        </div>
      </form>

      <div className="table-card">
        {scripts.length === 0 ? (
          <div className="empty-state">No saved scripts yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Preview</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {scripts.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>{s.script_text.length > 80 ? `${s.script_text.slice(0, 80)}…` : s.script_text}</td>
                  <td>
                    <div className="row">
                      <button type="button" className="btn-secondary btn-sm" onClick={() => startEditScript(s)}>
                        Edit
                      </button>
                      <button type="button" className="btn-danger btn-sm" onClick={() => deleteScript(s.id)}>
                        Delete
                      </button>
                    </div>
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

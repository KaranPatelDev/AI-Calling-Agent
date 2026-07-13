import { useEffect, useState } from "react";

import { api } from "../api.js";
import ScriptEditor from "../components/ScriptEditor.jsx";

export default function Settings() {
  const [buyerScript, setBuyerScript] = useState("");
  const [sellerScript, setSellerScript] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    api
      .getScriptSettings()
      .then((s) => {
        setBuyerScript(s.buyer_script || "");
        setSellerScript(s.seller_script || "");
      })
      .catch((err) => setStatus(`Failed to load: ${err.message}`))
      .finally(() => setLoading(false));
  }, []);

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setStatus("");
    try {
      await api.saveScriptSettings({ buyer_script: buyerScript, seller_script: sellerScript });
      setStatus("Saved.");
    } catch (err) {
      setStatus(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
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

        <div className="row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
          {status && <p className="status">{status}</p>}
        </div>
      </form>
    </div>
  );
}

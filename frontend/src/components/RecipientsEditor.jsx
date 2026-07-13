import { useState } from "react";

import { api } from "../api.js";

export default function RecipientsEditor({ recipients, setRecipients }) {
  const [uploadStatus, setUploadStatus] = useState("");

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadStatus("Parsing file...");
    try {
      const parsed = await api.parseUpload(file);
      if (parsed.length) setRecipients(parsed);
      setUploadStatus(`Parsed ${parsed.length} recipient(s).`);
    } catch (err) {
      setUploadStatus(`Upload failed: ${err.message}`);
    }
  }

  function updateRecipient(i, field, value) {
    setRecipients((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRecipients((prev) => [...prev, { name: "", phone: "", organization: "" }]);
  }

  function removeRow(i) {
    setRecipients((prev) => prev.filter((_, idx) => idx !== i));
  }

  return (
    <>
      <div className="field-group">
        <label className="field-label">Upload recipients</label>
        <p className="field-hint">
          PDF, Excel (.xlsx), or CSV — parsed into the list below for you to review. An organization/company column
          is picked up automatically if present.
        </p>
        <input type="file" accept=".pdf,.xlsx,.xls,.csv" onChange={handleFile} />
        {uploadStatus && <p className="status">{uploadStatus}</p>}
      </div>

      <div className="field-group">
        <label className="field-label">Recipients ({recipients.length})</label>
        {recipients.map((r, i) => (
          <div className="recipient-row" key={i}>
            <input placeholder="Name" value={r.name} onChange={(e) => updateRecipient(i, "name", e.target.value)} />
            <input
              placeholder="Organization (optional)"
              value={r.organization || ""}
              onChange={(e) => updateRecipient(i, "organization", e.target.value)}
            />
            <input
              placeholder="Phone (+1...)"
              value={r.phone}
              onChange={(e) => updateRecipient(i, "phone", e.target.value)}
            />
            <button type="button" className="btn-ghost btn-sm" onClick={() => removeRow(i)}>
              Remove
            </button>
          </div>
        ))}
        <button type="button" className="btn-secondary btn-sm" onClick={addRow} style={{ alignSelf: "flex-start" }}>
          + Add recipient
        </button>
      </div>
    </>
  );
}

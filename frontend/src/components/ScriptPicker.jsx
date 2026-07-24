import { useEffect, useState } from "react";

import { api } from "../api.js";

export default function ScriptPicker({ onChange }) {
  const [scripts, setScripts] = useState([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    api.listScripts().then(setScripts).catch(() => {});
  }, []);

  function handleSelect(e) {
    const id = e.target.value;
    setSelected(id);
    const script = scripts.find((s) => s.id === id);
    if (script) onChange(script.script_text);
  }

  if (scripts.length === 0) return null;

  return (
    <div className="field-group">
      <label className="field-label">Use a saved script</label>
      <p className="field-hint">Pick one from your library, or just type/edit a script below.</p>
      <select value={selected} onChange={handleSelect}>
        <option value="" disabled>
          Choose a saved script…
        </option>
        {scripts.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
    </div>
  );
}

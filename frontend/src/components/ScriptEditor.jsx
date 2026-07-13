import { useRef } from "react";

const PLACEHOLDERS = [
  { token: "{{name}}", label: "Recipient name" },
  { token: "{{company}}", label: "Organization" },
];

export default function ScriptEditor({ value, onChange, label = "Script" }) {
  const textareaRef = useRef(null);

  function insertPlaceholder(token) {
    const el = textareaRef.current;
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    const next = value.slice(0, start) + token + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      el.focus();
      const cursor = start + token.length;
      el.setSelectionRange(cursor, cursor);
    });
  }

  return (
    <div className="field-group">
      <label className="field-label">{label}</label>
      <p className="field-hint">
        Exactly what should be read aloud on the call. Use placeholders to personalize each call automatically.
      </p>
      <div className="row">
        {PLACEHOLDERS.map((p) => (
          <button
            type="button"
            key={p.token}
            className="btn-secondary btn-sm"
            onClick={() => insertPlaceholder(p.token)}
          >
            Insert {p.token} <span style={{ opacity: 0.65 }}>({p.label})</span>
          </button>
        ))}
      </div>
      <textarea
        ref={textareaRef}
        rows={6}
        placeholder="Hi {{name}}, this is a reminder from {{company}}..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

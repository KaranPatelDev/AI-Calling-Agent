const OPTIONS = [
  { value: "buyer", label: "Buyers" },
  { value: "seller", label: "Sellers" },
];

export default function AudienceToggle({ value, onChange }) {
  return (
    <div className="field-group">
      <label className="field-label">Audience</label>
      <div className="row">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={value === opt.value ? "btn-audience active" : "btn-audience"}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

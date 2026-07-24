export default function Tabs({ options, value, onChange }) {
  return (
    <div className="tabs">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={value === opt.value ? "tab active" : "tab"}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

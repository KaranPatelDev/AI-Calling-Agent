export default function SpeedControl({ value, onChange }) {
  return (
    <div className="field-group">
      <label className="field-label">Speaking speed (optional)</label>
      <p className="field-hint">
        Leave blank to use your default speed from Settings. Lower % = slower.
      </p>
      <div className="row">
        <input
          type="number"
          min="40"
          max="120"
          placeholder="Default"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value === "" ? "" : e.target.value)}
          style={{ width: "6rem" }}
        />
        <span>%</span>
      </div>
    </div>
  );
}

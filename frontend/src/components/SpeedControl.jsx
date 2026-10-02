import { useState } from "react";

const MIN_RATE = 40;
// Polly's hard ceiling is 200%, but only for standard voices (neural caps near 150%) and
// Polly.Aditi — the only Hindi voice Plivo reliably supports — turns clipped/chipmunky past
// ~150, so cap there even though the provider would accept more.
const MAX_RATE = 150;

function describe(rate) {
  if (rate === "" || rate == null) return "";
  const n = Number(rate);
  if (!Number.isFinite(n)) return "";
  const delta = n - 100;
  if (delta === 0) return "normal speed";
  return `${Math.abs(delta)}% ${delta > 0 ? "faster" : "slower"}`;
}

export default function SpeedControl({ value, onChange }) {
  // Two separate raw inputs so mid-keystroke partial values (e.g. "1" on the way to "125")
  // are held locally and don't clobber each other. Typing in one clears the other.
  const initN = value === "" || value == null ? null : Number(value);
  const [slowerRaw, setSlowerRaw] = useState(
    () => (initN != null && initN < 100 ? String(initN) : "")
  );
  const [fasterRaw, setFasterRaw] = useState(
    () => (initN != null && initN > 100 ? String(initN) : "")
  );

  function handleSlower(raw) {
    setSlowerRaw(raw);
    setFasterRaw("");
    if (raw === "") return onChange("");
    const n = Number(raw);
    if (Number.isFinite(n)) onChange(raw);
  }

  function handleFaster(raw) {
    setFasterRaw(raw);
    setSlowerRaw("");
    if (raw === "") return onChange("");
    const n = Number(raw);
    if (Number.isFinite(n) && n > MAX_RATE) {
      setFasterRaw(String(MAX_RATE));
      return onChange(String(MAX_RATE));
    }
    if (Number.isFinite(n)) onChange(raw);
  }

  const numVal = value === "" || value == null ? null : Number(value);
  const belowMin = numVal != null && numVal < MIN_RATE;
  const label = describe(value);

  return (
    <div className="field-group">
      <label className="field-label">Speaking speed (optional)</label>
      <p className="field-hint">
        Leave blank to use your default speed from Settings. 100% = normal speed.
      </p>
      <div className="row" style={{ alignItems: "flex-start", gap: "1.5rem" }}>
        <div>
          <p className="field-hint" style={{ marginBottom: "0.25rem" }}>
            Slower (40–99%)
          </p>
          <div className="row">
            <input
              type="number"
              min={MIN_RATE}
              max={99}
              placeholder="Default"
              value={slowerRaw}
              onChange={(e) => handleSlower(e.target.value)}
              style={{ width: "6rem" }}
            />
            <span>%</span>
          </div>
          <p className="field-hint">Lower % = slower</p>
        </div>
        <div>
          <p className="field-hint" style={{ marginBottom: "0.25rem" }}>
            Faster (101–150%)
          </p>
          <div className="row">
            <input
              type="number"
              min={101}
              max={MAX_RATE}
              placeholder="Default"
              value={fasterRaw}
              onChange={(e) => handleFaster(e.target.value)}
              style={{ width: "6rem" }}
            />
            <span>%</span>
          </div>
          <p className="field-hint">Higher % = faster</p>
        </div>
        {label && <span className="field-hint" style={{ alignSelf: "center" }}>{label}</span>}
      </div>
      {belowMin && (
        <p className="field-hint">
          Minimum is {MIN_RATE}%. Calls below that will be rejected.
        </p>
      )}
    </div>
  );
}
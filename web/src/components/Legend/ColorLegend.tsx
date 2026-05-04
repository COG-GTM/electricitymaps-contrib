import {
  CARBON_INTENSITY_COLORS,
  CARBON_INTENSITY_DOMAIN,
} from "../../utils/colors";

export function ColorLegend() {
  const stops = CARBON_INTENSITY_DOMAIN.map((value, i) => ({
    value,
    color: CARBON_INTENSITY_COLORS[i],
    pct: (i / (CARBON_INTENSITY_DOMAIN.length - 1)) * 100,
  }));

  const gradient = stops.map((s) => `${s.color} ${s.pct}%`).join(", ");

  return (
    <div className="legend" aria-label="Carbon intensity legend">
      <div className="legend__title">Carbon intensity (gCO₂eq/kWh)</div>
      <div
        className="legend__bar"
        style={{ background: `linear-gradient(to right, ${gradient})` }}
      />
      <div className="legend__ticks">
        {CARBON_INTENSITY_DOMAIN.map((v, i) => (
          <span key={v} style={{ left: `${(i / (CARBON_INTENSITY_DOMAIN.length - 1)) * 100}%` }}>
            {v}
            {i === CARBON_INTENSITY_DOMAIN.length - 1 ? "+" : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

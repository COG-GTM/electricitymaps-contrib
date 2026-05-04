// Carbon intensity color scale (gCO2eq/kWh -> hex color).
//
// Stops chosen to match a typical green -> yellow -> orange -> red -> dark red
// gradient over 0-800+ gCO2eq/kWh.

export const CARBON_INTENSITY_DOMAIN = [0, 100, 200, 350, 500, 700, 900] as const;
export const CARBON_INTENSITY_COLORS = [
  "#2aa364", // 0   — very low (renewables)
  "#76b853", // 100
  "#d6cc1f", // 200
  "#e8932c", // 350
  "#d4582f", // 500
  "#a4382f", // 700
  "#5e1f24", // 900+
] as const;

export const NO_DATA_COLOR = "#3a3a45";

function hexToRgb(hex: string): [number, number, number] {
  const m = hex.replace("#", "");
  return [
    parseInt(m.slice(0, 2), 16),
    parseInt(m.slice(2, 4), 16),
    parseInt(m.slice(4, 6), 16),
  ];
}

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) =>
    Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

export function getCarbonIntensityColor(intensity: number | null | undefined): string {
  if (intensity == null || Number.isNaN(intensity)) return NO_DATA_COLOR;
  const v = Math.max(0, intensity);

  for (let i = 0; i < CARBON_INTENSITY_DOMAIN.length - 1; i++) {
    const lo = CARBON_INTENSITY_DOMAIN[i];
    const hi = CARBON_INTENSITY_DOMAIN[i + 1];
    if (v >= lo && v <= hi) {
      const t = (v - lo) / (hi - lo);
      const [r1, g1, b1] = hexToRgb(CARBON_INTENSITY_COLORS[i]);
      const [r2, g2, b2] = hexToRgb(CARBON_INTENSITY_COLORS[i + 1]);
      return rgbToHex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t);
    }
  }
  return CARBON_INTENSITY_COLORS[CARBON_INTENSITY_COLORS.length - 1];
}

// Per-mode colors used in production-mix charts. Aligned with common
// Electricity Maps palette.
export const MODE_COLORS: Record<string, string> = {
  solar: "#f5b800",
  wind: "#74cdf0",
  hydro: "#2772b2",
  "hydro storage": "#0b3d91",
  "hydro discharge": "#0b3d91",
  nuclear: "#a868a1",
  geothermal: "#bb8fce",
  biomass: "#7e9c5b",
  coal: "#3a3a3a",
  gas: "#bf6b04",
  oil: "#867a6b",
  "battery storage": "#7c7cd1",
  "battery discharge": "#7c7cd1",
  "unknown fossil": "#736b5e",
  "unknown renewable": "#9aa57a",
  unknown: "#888888",
};

export function getModeColor(mode: string): string {
  return MODE_COLORS[mode] ?? "#888888";
}

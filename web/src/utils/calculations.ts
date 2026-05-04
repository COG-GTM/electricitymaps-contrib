import type { ProductionMix } from "../types";

// Direct-emission factors per generation mode (gCO2eq/kWh).
// Values are conservative midpoints from public IPCC / EM literature; sufficient
// for visualization when carbonIntensity is missing from the dataset.
export const EMISSION_FACTORS: Record<string, number> = {
  coal: 820,
  gas: 490,
  oil: 650,
  biomass: 230,
  geothermal: 38,
  solar: 45,
  wind: 11,
  nuclear: 12,
  hydro: 24,
  "hydro storage": 24,
  "hydro discharge": 24,
  "battery storage": 0,
  "battery discharge": 0,
  unknown: 700,
  "unknown fossil": 700,
  "unknown renewable": 30,
};

export function computeCarbonIntensity(mix: ProductionMix): number {
  let totalMW = 0;
  let weighted = 0;
  for (const [mode, value] of Object.entries(mix)) {
    if (value == null || value <= 0) continue;
    const factor = EMISSION_FACTORS[mode] ?? 700;
    totalMW += value;
    weighted += value * factor;
  }
  if (totalMW <= 0) return 0;
  return weighted / totalMW;
}

export function totalProduction(mix: ProductionMix): number {
  let total = 0;
  for (const value of Object.values(mix)) {
    if (value != null && value > 0) total += value;
  }
  return total;
}

export function carbonFreePercent(mix: ProductionMix): number {
  const carbonFreeModes = new Set([
    "solar",
    "wind",
    "hydro",
    "hydro storage",
    "hydro discharge",
    "nuclear",
    "geothermal",
    "battery discharge",
  ]);
  const total = totalProduction(mix);
  if (total <= 0) return 0;
  let cf = 0;
  for (const [mode, value] of Object.entries(mix)) {
    if (value != null && value > 0 && carbonFreeModes.has(mode)) cf += value;
  }
  return (cf / total) * 100;
}

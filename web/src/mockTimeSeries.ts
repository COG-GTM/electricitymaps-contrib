import type { ProductionMix, TimeSeriesPoint, ZoneMockData } from './types';

const CO2_FACTORS: Record<string, number> = {
  nuclear: 12,
  wind: 11,
  solar: 45,
  hydro: 24,
  'hydro storage': 24,
  'hydro discharge': 24,
  'battery discharge': 50,
  'battery storage': 50,
  gas: 380,
  coal: 820,
  oil: 650,
  biomass: 230,
  geothermal: 38,
  unknown: 200,
  'unknown fossil': 700,
  'unknown renewable': 50,
};

function hashCode(s: string): number {
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    const char = s.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return Math.abs(hash);
}

function pseudoRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

const STABLE_MODES = new Set(['nuclear', 'geothermal', 'biomass']);

const SOLAR_MODES = new Set(['solar']);
const WIND_MODES = new Set(['wind']);
const DEMAND_MODES = new Set(['gas', 'coal', 'oil']);

/**
 * Build a single synthetic point for a given timestamp using the zone's
 * current mock production as a base. Solar follows a daylight curve, wind
 * uses a sinusoid, fossil fuels follow demand, and stable modes vary little.
 * Carbon intensity is recomputed from the resulting mix.
 *
 * The pseudo-random offsets are deterministic per (zoneKey, hour-bucket) so
 * the same timestamp always produces the same production breakdown.
 */
export function buildSyntheticPoint(
  zoneKey: string,
  baseData: ZoneMockData,
  dt: Date,
): TimeSeriesPoint {
  const seed = hashCode(zoneKey);
  // Deterministic per-hour bucket (independent of arbitrary anchor).
  const hourBucket = Math.floor(dt.getTime() / 3_600_000);
  const hour = dt.getUTCHours();

  const solarFactor = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI));
  const windFactor =
    0.5 +
    0.5 * Math.sin((hour / 24) * Math.PI * 2 + pseudoRandom(seed + hourBucket) * 2);
  const demandFactor = 0.7 + 0.3 * Math.sin(((hour - 4) / 24) * Math.PI * 2);

  const production: ProductionMix = {};
  let modeIdx = 0;
  for (const [mode, base] of Object.entries(baseData.production)) {
    modeIdx++;
    let val = base;
    if (SOLAR_MODES.has(mode)) {
      val = base * solarFactor;
    } else if (WIND_MODES.has(mode)) {
      val =
        base *
        windFactor *
        (0.5 + pseudoRandom(seed + hourBucket * 3 + modeIdx) * 1);
    } else if (DEMAND_MODES.has(mode)) {
      val =
        base *
        demandFactor *
        (0.75 + pseudoRandom(seed + hourBucket * 7 + modeIdx) * 0.5);
    } else if (STABLE_MODES.has(mode)) {
      val = base * (0.92 + pseudoRandom(seed + hourBucket * 11 + modeIdx) * 0.16);
    } else {
      val = base * (0.7 + pseudoRandom(seed + hourBucket * 13 + modeIdx) * 0.6);
    }
    production[mode] = Math.max(0, Math.round(val * 100) / 100);
  }

  const total = Object.values(production).reduce((s, v) => s + v, 0);
  let ci = baseData.carbonIntensity;
  if (total > 0) {
    ci =
      Object.entries(production).reduce(
        (s, [k, v]) => s + v * (CO2_FACTORS[k] ?? 200),
        0,
      ) / total;
  }

  return {
    datetime: dt.toISOString(),
    carbonIntensity: Math.round(ci),
    production,
  };
}

/**
 * Build an `hours`-long synthetic hourly series for a zone, anchored to
 * `anchor` (defaulting to "now"). The anchor is rounded down to the nearest
 * hour so the grid is stable across renders.
 *
 * Returns exactly `hours` points (most recent first generated last, sorted
 * ascending by datetime).
 */
export function generateTimeSeries(
  zoneKey: string,
  baseData: ZoneMockData,
  hours: number = 48,
  anchor: Date = new Date(),
): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = [];
  const anchorMs = Math.floor(anchor.getTime() / 3_600_000) * 3_600_000;
  for (let i = hours - 1; i >= 0; i--) {
    const dt = new Date(anchorMs - i * 3_600_000);
    points.push(buildSyntheticPoint(zoneKey, baseData, dt));
  }
  return points;
}

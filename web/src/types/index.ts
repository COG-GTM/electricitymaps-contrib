// TypeScript interfaces mirroring the JSON data produced by
// web/scripts/generate_web_data.py and generate_real_data.py.

export interface ZoneConfig {
  zoneName: string;
  countryKey: string | null;
  countryName: string;
  region: string;
  timezone: string;
}

export type ZonesMap = Record<string, ZoneConfig>;

export interface ExchangeConfig {
  zones: [string, string];
  lonlat: [number, number];
  rotation: number;
}

export type ExchangesMap = Record<string, ExchangeConfig>;

// Production breakdown by generation mode (in MW). Modes mirror the keys used
// in config/zones/*.yaml capacity blocks.
export interface ProductionMix {
  solar?: number | null;
  wind?: number | null;
  coal?: number | null;
  gas?: number | null;
  nuclear?: number | null;
  hydro?: number | null;
  biomass?: number | null;
  geothermal?: number | null;
  oil?: number | null;
  unknown?: number | null;
  "battery storage"?: number | null;
  "hydro storage"?: number | null;
  "hydro discharge"?: number | null;
  "battery discharge"?: number | null;
  "unknown fossil"?: number | null;
  "unknown renewable"?: number | null;
  [mode: string]: number | null | undefined;
}

export interface ZoneSnapshot {
  carbonIntensity: number;
  carbonFree: number;
  renewable: number;
  totalProduction: number;
  production: ProductionMix;
  isEstimated: boolean;
}

export interface CarbonIntensityPoint {
  datetime: string;
  carbonIntensity: number;
}

export interface GridDataFile {
  timestamp: string;
  zones: Record<string, ZoneSnapshot>;
  timeseries: Record<string, CarbonIntensityPoint[]>;
}

export interface ZoneGridData extends ZoneSnapshot {
  zoneKey: string;
  datetime: string;
}

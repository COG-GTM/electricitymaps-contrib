export interface ZoneInfo {
  zoneName: string;
  countryKey: string | null;
  countryName: string;
  region: string;
  timezone: string;
}

// Real captured data has dynamic mode keys (e.g. "hydro storage", "battery discharge").
export type ProductionMix = Record<string, number>;

export interface ZoneMockData {
  carbonIntensity: number;
  carbonFree: number;
  renewable: number;
  totalProduction: number;
  production: ProductionMix;
  isEstimated: boolean;
}

export interface ExchangeInfo {
  zones: string[];
  lonlat: [number, number];
  rotation: number;
}

export type Resolution =
  | 'five_minutes'
  | 'fifteen_minutes'
  | 'hourly'
  | 'daily'
  | 'monthly'
  | 'yearly';

export interface TimeSeriesPoint {
  datetime: string;
  carbonIntensity: number;
  production?: ProductionMix;
}

export interface RealDataFile {
  timestamp: string;
  zones: Record<string, ZoneMockData>;
  timeseries: Record<string, { datetime: string; carbonIntensity: number }[]>;
}

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  ExchangesMap,
  GridDataFile,
  ZoneGridData,
  ZonesMap,
  ZoneSnapshot,
} from "../types";
import { useExchanges } from "../hooks/useExchanges";
import { useGridData } from "../hooks/useGridData";
import { useZones } from "../hooks/useZones";

interface AppContextValue {
  zones: ZonesMap | null;
  exchanges: ExchangesMap | null;
  gridData: GridDataFile | null;

  loading: boolean;
  error: Error | null;

  selectedZone: string | null;
  setSelectedZone: (zone: string | null) => void;

  // Sorted ascending list of all distinct datetimes available across all zone
  // timeseries — used to drive the time slider.
  datetimes: string[];
  selectedDatetime: string | null;
  setSelectedDatetime: (dt: string) => void;

  // Resolved snapshot for a zone at the currently selected datetime (falling
  // back to the latest snapshot in `zones`).
  getZoneSnapshot: (zoneKey: string) => ZoneGridData | null;
  getZoneIntensity: (zoneKey: string) => number | null;
}

const AppContext = createContext<AppContextValue | null>(null);

function deriveDatetimes(grid: GridDataFile | null): string[] {
  if (!grid) return [];
  const set = new Set<string>();
  for (const series of Object.values(grid.timeseries)) {
    for (const point of series) set.add(point.datetime);
  }
  if (set.size === 0 && grid.timestamp) set.add(grid.timestamp);
  return [...set].sort();
}

export function AppProvider({ children }: { children: ReactNode }) {
  const zonesState = useZones();
  const exchangesState = useExchanges();
  const gridState = useGridData();

  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [selectedDatetime, setSelectedDatetimeState] = useState<string | null>(null);

  const datetimes = useMemo(() => deriveDatetimes(gridState.data), [gridState.data]);

  // Default the slider to the latest available datetime as soon as the grid
  // dataset arrives.
  if (selectedDatetime === null && datetimes.length > 0) {
    queueMicrotask(() => setSelectedDatetimeState(datetimes[datetimes.length - 1]));
  }

  const setSelectedDatetime = useCallback((dt: string) => {
    setSelectedDatetimeState(dt);
  }, []);

  // Pre-index per-zone timeseries by datetime for O(1) lookup while scrubbing.
  const tsIndex = useMemo(() => {
    const out = new Map<string, Map<string, number>>();
    if (!gridState.data) return out;
    for (const [zoneKey, series] of Object.entries(gridState.data.timeseries)) {
      const m = new Map<string, number>();
      for (const point of series) m.set(point.datetime, point.carbonIntensity);
      out.set(zoneKey, m);
    }
    return out;
  }, [gridState.data]);

  const getZoneIntensity = useCallback(
    (zoneKey: string): number | null => {
      const grid = gridState.data;
      if (!grid) return null;
      const dt = selectedDatetime ?? grid.timestamp;
      const tsValue = tsIndex.get(zoneKey)?.get(dt);
      if (typeof tsValue === "number") return tsValue;
      const snap = grid.zones[zoneKey];
      return snap?.carbonIntensity ?? null;
    },
    [gridState.data, selectedDatetime, tsIndex],
  );

  const getZoneSnapshot = useCallback(
    (zoneKey: string): ZoneGridData | null => {
      const grid = gridState.data;
      if (!grid) return null;
      const snap: ZoneSnapshot | undefined = grid.zones[zoneKey];
      if (!snap) return null;
      const dt = selectedDatetime ?? grid.timestamp;
      const intensity = tsIndex.get(zoneKey)?.get(dt) ?? snap.carbonIntensity;
      return { ...snap, carbonIntensity: intensity, zoneKey, datetime: dt };
    },
    [gridState.data, selectedDatetime, tsIndex],
  );

  const value: AppContextValue = {
    zones: zonesState.data,
    exchanges: exchangesState.data,
    gridData: gridState.data,
    loading: zonesState.loading || exchangesState.loading || gridState.loading,
    error: zonesState.error ?? exchangesState.error ?? gridState.error,
    selectedZone,
    setSelectedZone,
    datetimes,
    selectedDatetime,
    setSelectedDatetime,
    getZoneSnapshot,
    getZoneIntensity,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within AppProvider");
  return ctx;
}

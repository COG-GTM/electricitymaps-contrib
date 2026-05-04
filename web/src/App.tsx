import { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';
import MapView from './components/MapView';
import Sidebar from './components/Sidebar';
import ZonePanel from './components/ZonePanel';
import BottomBar from './components/BottomBar';
import CarbonLegend from './components/CarbonLegend';
import DateHeader from './components/DateHeader';
import SearchOverlay from './components/SearchOverlay';
import type {
  RealDataFile,
  Resolution,
  TimeSeriesPoint,
  ZoneInfo,
  ZoneMockData,
} from './types';
import { buildSyntheticPoint, generateTimeSeries } from './mockTimeSeries';

export default function App() {
  const [zones, setZones] = useState<Record<string, ZoneInfo>>({});
  const [mockData, setMockData] = useState<Record<string, ZoneMockData>>({});
  const [timeseries, setTimeseries] = useState<
    Record<string, { datetime: string; carbonIntensity: number }[]>
  >({});
  const [dataTimestamp, setDataTimestamp] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [resolution, setResolution] = useState<Resolution>('fifteen_minutes');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [zonesRes, dataRes] = await Promise.all([
          fetch('/zones.json'),
          fetch('/mock-data.json'),
        ]);
        if (!zonesRes.ok || !dataRes.ok) {
          throw new Error(
            `Failed to load data: zones=${zonesRes.status}, mock=${dataRes.status}`,
          );
        }
        const zonesJson = (await zonesRes.json()) as Record<string, ZoneInfo>;
        const dataJson = (await dataRes.json()) as Partial<RealDataFile> &
          Record<string, ZoneMockData>;
        if (cancelled) return;
        setZones(zonesJson);

        // Support both real-data shape ({ zones, timeseries }) and a flat
        // legacy shape ({ ZONE_KEY: ZoneMockData }).
        if (dataJson.zones && typeof dataJson.zones === 'object') {
          setMockData(dataJson.zones as Record<string, ZoneMockData>);
          setTimeseries(dataJson.timeseries ?? {});
          if (dataJson.timestamp) {
            setDataTimestamp(dataJson.timestamp);
            setCurrentTime(new Date(dataJson.timestamp));
          }
        } else {
          setMockData(dataJson as unknown as Record<string, ZoneMockData>);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : String(err));
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleZoneSelect = useCallback((zoneKey: string | null) => {
    setSelectedZone(zoneKey);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedZone(null);
  }, []);

  const handleSearchSelect = useCallback((zoneKey: string) => {
    setSelectedZone(zoneKey);
    setSearchOpen(false);
  }, []);

  // Build the carbon-intensity series for the selected zone. When captured
  // timeseries data is available, use its timestamps as the time axis and
  // pull a synthetic production breakdown for each one (the captured data
  // doesn't include a per-timestamp production breakdown). Otherwise fall
  // back to a fully synthetic 48h hourly series.
  const selectedSeries = useMemo<TimeSeriesPoint[]>(() => {
    if (!selectedZone) return [];
    const zd = mockData[selectedZone];
    if (!zd) return [];
    const captured = timeseries[selectedZone];
    if (captured && captured.length > 1) {
      return captured
        .slice()
        .sort((a, b) => (a.datetime < b.datetime ? -1 : 1))
        .map((p) => {
          const synth = buildSyntheticPoint(
            selectedZone,
            zd,
            new Date(p.datetime),
          );
          return {
            datetime: p.datetime,
            carbonIntensity: p.carbonIntensity,
            production: synth.production,
          };
        });
    }
    const anchor = dataTimestamp ? new Date(dataTimestamp) : new Date();
    return generateTimeSeries(selectedZone, zd, 48, anchor);
  }, [selectedZone, mockData, timeseries, dataTimestamp]);

  return (
    <div className="app">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((c) => !c)}
        onSearchClick={() => setSearchOpen(true)}
      />

      <main
        className="main-area"
        style={{
          left: sidebarCollapsed
            ? 'var(--sidebar-width-collapsed)'
            : 'var(--sidebar-width)',
        }}
      >
        <MapView
          mockData={mockData}
          selectedZone={selectedZone}
          onZoneSelect={handleZoneSelect}
        />

        <DateHeader currentTime={currentTime} resolution={resolution} />
        <CarbonLegend />

        {selectedZone && (
          <ZonePanel
            zoneKey={selectedZone}
            zoneInfo={zones[selectedZone]}
            data={mockData[selectedZone]}
            timeSeries={selectedSeries}
            onBack={handleBack}
          />
        )}

        <BottomBar
          currentTime={currentTime}
          onTimeChange={setCurrentTime}
          resolution={resolution}
          onResolutionChange={setResolution}
          dataTimestamp={dataTimestamp}
        />

        {loadError && (
          <div className="app__error">
            Failed to load data: {loadError}. Run{' '}
            <code>cd web/scripts && python generate_web_data.py</code> and
            <code> generate_real_data.py</code> from the repo root.
          </div>
        )}
      </main>

      {searchOpen && (
        <SearchOverlay
          zones={zones}
          mockData={mockData}
          onClose={() => setSearchOpen(false)}
          onSelect={handleSearchSelect}
        />
      )}
    </div>
  );
}

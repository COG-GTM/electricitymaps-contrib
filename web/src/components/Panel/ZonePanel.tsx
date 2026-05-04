import { useMemo } from "react";

import { useAppContext } from "../../context/AppContext";
import { computeCarbonIntensity } from "../../utils/calculations";
import { CarbonIntensityBadge } from "./CarbonIntensityBadge";
import { ProductionMixChart } from "./ProductionMixChart";

export function ZonePanel() {
  const { selectedZone, setSelectedZone, zones, getZoneSnapshot } = useAppContext();

  const snapshot = useMemo(() => {
    if (!selectedZone) return null;
    return getZoneSnapshot(selectedZone);
  }, [selectedZone, getZoneSnapshot]);

  if (!selectedZone) return null;

  const zoneCfg = zones?.[selectedZone];
  const computedIntensity = snapshot ? computeCarbonIntensity(snapshot.production) : null;
  const displayIntensity = snapshot?.carbonIntensity ?? computedIntensity ?? null;

  return (
    <aside className="zone-panel" role="dialog" aria-label="Zone details">
      <header className="zone-panel__header">
        <div>
          <div className="zone-panel__name">
            {zoneCfg?.zoneName ?? selectedZone}
          </div>
          <div className="zone-panel__meta">
            {zoneCfg?.countryName ?? selectedZone}
            {zoneCfg?.region ? ` · ${zoneCfg.region}` : ""}
            {zoneCfg?.timezone ? ` · ${zoneCfg.timezone}` : ""}
          </div>
        </div>
        <button
          type="button"
          className="zone-panel__close"
          aria-label="Close zone details"
          onClick={() => setSelectedZone(null)}
        >
          ×
        </button>
      </header>

      <CarbonIntensityBadge
        intensity={displayIntensity}
        isEstimated={snapshot?.isEstimated}
      />

      {snapshot ? (
        <>
          <div className="zone-panel__stats">
            <Stat
              label="Renewable"
              value={`${snapshot.renewable.toFixed(1)}%`}
            />
            <Stat
              label="Carbon free"
              value={`${snapshot.carbonFree.toFixed(1)}%`}
            />
            <Stat
              label="Total production"
              value={`${formatMW(snapshot.totalProduction)}`}
            />
          </div>

          <h3 className="zone-panel__h3">Production mix</h3>
          <ProductionMixChart mix={snapshot.production} />

          <div className="zone-panel__footer">
            Snapshot: {formatDt(snapshot.datetime)}
          </div>
        </>
      ) : (
        <div className="zone-panel__empty">No grid data for this zone.</div>
      )}
    </aside>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
    </div>
  );
}

function formatMW(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(1)} GW`;
  return `${Math.round(v)} MW`;
}

function formatDt(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

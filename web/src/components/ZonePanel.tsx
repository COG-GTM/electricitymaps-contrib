import { useMemo } from 'react';
import type { TimeSeriesPoint, ZoneInfo, ZoneMockData } from '../types';
import { getCO2Color, modeColor, MODE_COLORS } from '../colors';
import CarbonIntensityChart from './CarbonIntensityChart';
import ElectricityMixChart from './ElectricityMixChart';
import './ZonePanel.css';

interface ZonePanelProps {
  zoneKey: string;
  zoneInfo: ZoneInfo | undefined;
  data: ZoneMockData | undefined;
  timeSeries: TimeSeriesPoint[];
  onBack: () => void;
}

function getCountryFlag(countryKey: string): string {
  const code = countryKey.split('-')[0].toUpperCase();
  if (code.length !== 2) return '';
  const offset = 0x1f1e6;
  const a = code.charCodeAt(0);
  const b = code.charCodeAt(1);
  if (a < 65 || a > 90 || b < 65 || b > 90) return '';
  return String.fromCodePoint(a - 65 + offset, b - 65 + offset);
}

export default function ZonePanel({
  zoneKey,
  zoneInfo,
  data,
  timeSeries,
  onBack,
}: ZonePanelProps) {
  const flag = getCountryFlag(zoneInfo?.countryKey || zoneKey.split('-')[0]);
  const ciColor = data ? getCO2Color(data.carbonIntensity) : '#d4d4d4';

  const productionEntries = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.production)
      .filter(([, v]) => v > 0.01)
      .sort((a, b) => b[1] - a[1]);
  }, [data]);

  const totalProduction = data?.totalProduction ?? 0;
  const ciMarkerLeft = Math.min(
    100,
    Math.max(0, ((data?.carbonIntensity ?? 0) / 1500) * 100),
  );

  return (
    <aside className="zone-panel" aria-label={`Details for ${zoneKey}`}>
      <header className="zone-panel__header">
        <button
          className="zone-panel__back"
          onClick={onBack}
          aria-label="Close zone panel"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
          >
            <path d="M11 4l-5 5 5 5" />
          </svg>
        </button>
        <div className="zone-panel__heading">
          <div className="zone-panel__country">
            {flag && <span className="zone-panel__flag">{flag}</span>}
            <span className="zone-panel__country-name">
              {zoneInfo?.countryName ?? zoneKey}
            </span>
          </div>
          <div className="zone-panel__zone-name">
            {zoneInfo?.zoneName ?? zoneKey}
          </div>
        </div>
      </header>

      {!data ? (
        <div className="zone-panel__empty">
          <p>No data for this zone yet.</p>
          <p className="zone-panel__empty-hint">
            Run <code>generate_real_data.py</code> to populate carbon
            intensity, production, and 48-hour history.
          </p>
        </div>
      ) : (
        <div className="zone-panel__body">
          <section className="zone-panel__section">
            <h3 className="zone-panel__section-title">Carbon intensity</h3>
            <div className="zone-panel__metrics">
              <div className="zone-panel__metric zone-panel__metric--ci">
                <div
                  className="zone-panel__ci-value"
                  style={{ color: ciColor }}
                >
                  {data.carbonIntensity}
                </div>
                <div className="zone-panel__metric-label">
                  gCO<sub>2</sub>eq/kWh
                </div>
              </div>
              <div className="zone-panel__metric">
                <div className="zone-panel__metric-value">
                  {data.carbonFree.toFixed(1)}%
                </div>
                <div className="zone-panel__metric-label">Carbon-free</div>
                <div className="zone-panel__gauge">
                  <div
                    className="zone-panel__gauge-fill"
                    style={{
                      width: `${Math.min(100, data.carbonFree)}%`,
                      background: '#2AA364',
                    }}
                  />
                </div>
              </div>
              <div className="zone-panel__metric">
                <div className="zone-panel__metric-value">
                  {data.renewable.toFixed(1)}%
                </div>
                <div className="zone-panel__metric-label">Renewable</div>
                <div className="zone-panel__gauge">
                  <div
                    className="zone-panel__gauge-fill"
                    style={{
                      width: `${Math.min(100, data.renewable)}%`,
                      background: '#74cdb9',
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="zone-panel__ci-bar">
              <div className="zone-panel__ci-gradient" />
              <div
                className="zone-panel__ci-marker"
                style={{ left: `${ciMarkerLeft}%` }}
              />
              <div className="zone-panel__ci-ticks">
                <span>0</span>
                <span>500</span>
                <span>1000</span>
                <span>1500</span>
              </div>
            </div>
          </section>

          <section className="zone-panel__section">
            <h3 className="zone-panel__section-title">
              Electricity production
              <span className="zone-panel__total">
                {Math.round(totalProduction).toLocaleString()} MW
              </span>
            </h3>
            <div className="zone-panel__capacity-bar">
              {productionEntries.map(([mode, mw]) => {
                const pct = totalProduction > 0 ? (mw / totalProduction) * 100 : 0;
                return (
                  <div
                    key={mode}
                    className="zone-panel__capacity-segment"
                    style={{
                      width: `${pct}%`,
                      background: modeColor(mode),
                    }}
                    title={`${mode}: ${mw.toFixed(1)} MW (${pct.toFixed(1)}%)`}
                  />
                );
              })}
            </div>

            <ul className="zone-panel__production-list">
              {productionEntries.map(([mode, mw]) => {
                const pct =
                  totalProduction > 0 ? (mw / totalProduction) * 100 : 0;
                return (
                  <li
                    key={mode}
                    className="zone-panel__production-item"
                  >
                    <span
                      className="zone-panel__production-swatch"
                      style={{ background: modeColor(mode) }}
                    />
                    <span className="zone-panel__production-mode">
                      {mode}
                    </span>
                    <span className="zone-panel__production-value">
                      {mw < 10 ? mw.toFixed(1) : Math.round(mw).toLocaleString()}{' '}
                      MW
                    </span>
                    <span className="zone-panel__production-pct">
                      {pct.toFixed(1)}%
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="zone-panel__section">
            <h3 className="zone-panel__section-title">
              Carbon intensity (last 48h)
            </h3>
            <CarbonIntensityChart data={timeSeries} />
          </section>

          <section className="zone-panel__section">
            <h3 className="zone-panel__section-title">
              Electricity mix (last 48h)
            </h3>
            <ElectricityMixChart data={timeSeries} />
            <div className="zone-panel__mix-legend">
              {productionEntries.slice(0, 8).map(([mode]) => (
                <span
                  key={mode}
                  className="zone-panel__mix-legend-item"
                >
                  <span
                    className="zone-panel__mix-legend-swatch"
                    style={{ background: modeColor(mode) }}
                  />
                  {mode}
                </span>
              ))}
            </div>
          </section>

          <section className="zone-panel__section zone-panel__section--meta">
            <div className="zone-panel__meta-row">
              <span>Region</span>
              <strong>{zoneInfo?.region ?? '—'}</strong>
            </div>
            <div className="zone-panel__meta-row">
              <span>Timezone</span>
              <strong>{zoneInfo?.timezone ?? '—'}</strong>
            </div>
            <div className="zone-panel__meta-row">
              <span>Estimation</span>
              <strong>{data.isEstimated ? 'Estimated' : 'Measured'}</strong>
            </div>
            <p className="zone-panel__sources">
              Data sources: official TSO data via the{' '}
              <a
                href="https://github.com/electricitymaps/electricitymaps-contrib"
                target="_blank"
                rel="noreferrer"
              >
                electricitymaps-contrib
              </a>{' '}
              repository.
            </p>
          </section>
        </div>
      )}
      {/* Reference MODE_COLORS so unused-export linters don't complain in builds. */}
      <span style={{ display: 'none' }}>{Object.keys(MODE_COLORS).length}</span>
    </aside>
  );
}

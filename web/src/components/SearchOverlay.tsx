import { useEffect, useMemo, useRef, useState } from 'react';
import type { ZoneInfo, ZoneMockData } from '../types';
import { getCO2Color } from '../colors';
import './SearchOverlay.css';

interface SearchOverlayProps {
  zones: Record<string, ZoneInfo>;
  mockData: Record<string, ZoneMockData>;
  onClose: () => void;
  onSelect: (zoneKey: string) => void;
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

export default function SearchOverlay({
  zones,
  mockData,
  onClose,
  onSelect,
}: SearchOverlayProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const all = Object.entries(zones).map(([key, info]) => ({ key, info }));
    if (!q) {
      return all
        .filter(({ key }) => mockData[key])
        .sort(
          (a, b) =>
            (mockData[b.key]?.carbonIntensity ?? 0) -
            (mockData[a.key]?.carbonIntensity ?? 0),
        )
        .slice(0, 80);
    }
    return all
      .filter(({ key, info }) => {
        return (
          key.toLowerCase().includes(q) ||
          info.zoneName?.toLowerCase().includes(q) ||
          info.countryName?.toLowerCase().includes(q)
        );
      })
      .slice(0, 80);
  }, [query, zones, mockData]);

  return (
    <div
      className="search-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="search-overlay__panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="search-overlay__input-row">
          <svg
            width="18"
            height="18"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="9" cy="9" r="6" />
            <path d="M14 14l4 4" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search zones, countries..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            className="search-overlay__close"
            onClick={onClose}
            aria-label="Close search"
          >
            ESC
          </button>
        </div>

        <ul className="search-overlay__results">
          {results.length === 0 && (
            <li className="search-overlay__empty">No zones match.</li>
          )}
          {results.map(({ key, info }) => {
            const data = mockData[key];
            const flag = info.countryKey
              ? getCountryFlag(info.countryKey)
              : getCountryFlag(key);
            const ci = data?.carbonIntensity;
            return (
              <li key={key}>
                <button
                  className="search-overlay__result"
                  onClick={() => onSelect(key)}
                >
                  <span className="search-overlay__flag">{flag}</span>
                  <span className="search-overlay__zone">
                    <span className="search-overlay__zone-name">
                      {info.countryName || info.zoneName || key}
                    </span>
                    <span className="search-overlay__zone-key">
                      {info.zoneName && info.zoneName !== info.countryName
                        ? `${info.zoneName} · ${key}`
                        : key}
                    </span>
                  </span>
                  {ci != null ? (
                    <span
                      className="search-overlay__ci"
                      style={{ background: getCO2Color(ci) }}
                    >
                      {ci}
                    </span>
                  ) : (
                    <span className="search-overlay__ci search-overlay__ci--empty">
                      —
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

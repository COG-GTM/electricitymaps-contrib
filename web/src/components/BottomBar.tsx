import { useMemo } from 'react';
import type { Resolution } from '../types';
import './BottomBar.css';

interface BottomBarProps {
  currentTime: Date;
  onTimeChange: (date: Date) => void;
  resolution: Resolution;
  onResolutionChange: (r: Resolution) => void;
  dataTimestamp: string | null;
}

const RESOLUTION_OPTIONS: { value: Resolution; label: string }[] = [
  { value: 'five_minutes', label: '5 min' },
  { value: 'fifteen_minutes', label: '15 min' },
  { value: 'hourly', label: '1 hour' },
  { value: 'daily', label: '1 day' },
  { value: 'monthly', label: '1 month' },
  { value: 'yearly', label: '1 year' },
];

const WINDOW_HOURS = 48;

interface Tick {
  position: number; // 0-1
  label: string;
  showLabel: boolean;
}

function generateTimeTicks(start: Date, end: Date): Tick[] {
  const ticks: Tick[] = [];
  const totalMs = end.getTime() - start.getTime();
  if (totalMs <= 0) return ticks;
  const stepHours = 6;
  let prevDateLabel = '';
  for (
    let t = start.getTime();
    t <= end.getTime();
    t += stepHours * 60 * 60 * 1000
  ) {
    const dt = new Date(t);
    const hour = dt.getUTCHours();
    const dateLabel = dt.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    });
    let label: string;
    let showLabel = true;
    if (dateLabel !== prevDateLabel) {
      label = dateLabel;
      prevDateLabel = dateLabel;
    } else if (hour % 12 === 0) {
      label = `${hour.toString().padStart(2, '0')}:00`;
    } else {
      label = `${hour.toString().padStart(2, '0')}:00`;
      showLabel = false;
    }
    ticks.push({ position: (t - start.getTime()) / totalMs, label, showLabel });
  }
  return ticks;
}

export default function BottomBar({
  currentTime,
  onTimeChange,
  resolution,
  onResolutionChange,
  dataTimestamp,
}: BottomBarProps) {
  const { start, end, sliderValue } = useMemo(() => {
    const anchor = dataTimestamp ? new Date(dataTimestamp) : new Date();
    const startDate = new Date(anchor.getTime() - WINDOW_HOURS * 3600 * 1000);
    const endDate = anchor;
    const total = endDate.getTime() - startDate.getTime();
    const value = total > 0
      ? Math.max(
          0,
          Math.min(
            1000,
            Math.round(((currentTime.getTime() - startDate.getTime()) / total) * 1000),
          ),
        )
      : 1000;
    return { start: startDate, end: endDate, sliderValue: value };
  }, [currentTime, dataTimestamp]);

  const ticks = useMemo(() => generateTimeTicks(start, end), [start, end]);

  const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseInt(e.target.value, 10);
    const t = start.getTime() + (v / 1000) * (end.getTime() - start.getTime());
    onTimeChange(new Date(t));
  };

  const dateLabel = currentTime.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
  const timeLabel = currentTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });

  return (
    <div className="bottom-bar">
      <div className="bottom-bar__left">
        <div className="bottom-bar__date">
          <strong>{dateLabel}</strong>
          <span>{timeLabel} UTC</span>
        </div>
      </div>

      <div className="bottom-bar__slider">
        <input
          type="range"
          min={0}
          max={1000}
          value={sliderValue}
          onChange={handleSlider}
          className="bottom-bar__range"
          aria-label="Time slider"
        />
        <div className="bottom-bar__ticks">
          {ticks.map((tick, i) => (
            <span
              key={i}
              className="bottom-bar__tick"
              style={{ left: `${tick.position * 100}%` }}
            >
              {tick.showLabel ? tick.label : ''}
            </span>
          ))}
        </div>
      </div>

      <div className="bottom-bar__right">
        <label className="bottom-bar__resolution">
          <span>Resolution</span>
          <select
            value={resolution}
            onChange={(e) =>
              onResolutionChange(e.target.value as Resolution)
            }
          >
            {RESOLUTION_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}

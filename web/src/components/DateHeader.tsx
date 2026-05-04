import type { Resolution } from '../types';
import './DateHeader.css';

interface DateHeaderProps {
  currentTime: Date;
  resolution?: Resolution;
}

const RESOLUTION_LABEL: Record<Resolution, string> = {
  five_minutes: 'Live · 5m',
  fifteen_minutes: 'Live · 15m',
  hourly: 'Live · 1h',
  daily: 'Live · 24h',
  monthly: 'Live · 30d',
  yearly: 'Live · 1y',
};

export default function DateHeader({
  currentTime,
  resolution = 'fifteen_minutes',
}: DateHeaderProps) {
  const dateStr = currentTime.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
  const timeStr = currentTime.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'UTC',
  });

  return (
    <div className="date-header" role="status">
      <span className="date-header__live" />
      <span className="date-header__label">
        {RESOLUTION_LABEL[resolution]}
      </span>
      <span className="date-header__sep" />
      <span className="date-header__date">{dateStr}</span>
      <span className="date-header__time">{timeStr} UTC</span>
    </div>
  );
}

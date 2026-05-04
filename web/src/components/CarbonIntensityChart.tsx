import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TimeSeriesPoint } from '../types';
import { getCO2Color } from '../colors';

interface Props {
  data: TimeSeriesPoint[];
}

function formatHour(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', {
    hour: 'numeric',
    timeZone: 'UTC',
    hour12: false,
  });
}

function formatTooltip(label: unknown): string {
  if (typeof label !== 'string' && typeof label !== 'number') return '';
  const d = new Date(label);
  if (Number.isNaN(d.getTime())) return String(label);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });
}

export default function CarbonIntensityChart({ data }: Props) {
  const chartData = useMemo(
    () =>
      data.map((p) => ({
        datetime: p.datetime,
        carbonIntensity: p.carbonIntensity,
      })),
    [data],
  );

  const maxCi = useMemo(
    () =>
      chartData.reduce((m, p) => Math.max(m, p.carbonIntensity), 0) || 100,
    [chartData],
  );
  const stopColorLow = getCO2Color(Math.min(maxCi * 0.4, 200));
  const stopColorHigh = getCO2Color(maxCi);

  if (chartData.length === 0) {
    return <div className="chart-empty">No time series data.</div>;
  }

  return (
    <div className="chart-wrapper" style={{ height: 140 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 6, right: 8, left: -16, bottom: 0 }}
        >
          <defs>
            <linearGradient id="ci-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stopColorHigh} stopOpacity={0.7} />
              <stop offset="100%" stopColor={stopColorLow} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e5e7eb"
            vertical={false}
          />
          <XAxis
            dataKey="datetime"
            tickFormatter={formatHour}
            interval="preserveStartEnd"
            minTickGap={32}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            stroke="#e5e7eb"
          />
          <YAxis
            width={36}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            stroke="#e5e7eb"
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: '1px solid #e5e7eb',
            }}
            labelFormatter={formatTooltip}
            formatter={(value) => [`${value} gCO\u2082eq/kWh`, 'Carbon intensity']}
          />
          <Area
            type="monotone"
            dataKey="carbonIntensity"
            stroke={stopColorHigh}
            strokeWidth={2}
            fill="url(#ci-grad)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

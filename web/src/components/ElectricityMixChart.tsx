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
import { MIX_RENDER_ORDER, modeColor } from '../colors';

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

export default function ElectricityMixChart({ data }: Props) {
  const { rows, modes } = useMemo(() => {
    const modesPresent = new Set<string>();
    for (const p of data) {
      if (p.production) {
        for (const k of Object.keys(p.production)) modesPresent.add(k);
      }
    }
    const orderedKnown = MIX_RENDER_ORDER.filter((m) => modesPresent.has(m));
    const remaining = Array.from(modesPresent).filter(
      (m) => !MIX_RENDER_ORDER.includes(m),
    );
    const finalModes = [...orderedKnown, ...remaining];
    const buildRow = (p: TimeSeriesPoint): Record<string, number | string> => {
      const row: Record<string, number | string> = { datetime: p.datetime };
      for (const m of finalModes) {
        row[m] = p.production?.[m] ?? 0;
      }
      return row;
    };
    return { rows: data.map(buildRow), modes: finalModes };
  }, [data]);

  if (rows.length === 0 || modes.length === 0) {
    return <div className="chart-empty">No production breakdown.</div>;
  }

  return (
    <div className="chart-wrapper" style={{ height: 160 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={rows}
          margin={{ top: 6, right: 8, left: -16, bottom: 0 }}
        >
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
            width={48}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
            stroke="#e5e7eb"
            tickFormatter={(v) =>
              Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${v}`
            }
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: '1px solid #e5e7eb',
              maxHeight: 200,
              overflow: 'auto',
            }}
            labelFormatter={formatTooltip}
            formatter={(value, name) => [
              `${Math.round(Number(value)).toLocaleString()} MW`,
              name,
            ]}
          />
          {modes.map((mode) => (
            <Area
              key={mode}
              type="monotone"
              dataKey={mode}
              stackId="1"
              stroke={modeColor(mode)}
              fill={modeColor(mode)}
              fillOpacity={0.85}
              strokeWidth={0.6}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

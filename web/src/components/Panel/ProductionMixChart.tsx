import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import type { ProductionMix } from "../../types";
import { getModeColor } from "../../utils/colors";

interface Props {
  mix: ProductionMix;
}

export function ProductionMixChart({ mix }: Props) {
  const entries = Object.entries(mix)
    .filter(([, v]) => typeof v === "number" && v > 0)
    .map(([mode, value]) => ({ mode, value: value as number }))
    .sort((a, b) => b.value - a.value);

  if (entries.length === 0) {
    return <div className="prod-empty">No production breakdown available.</div>;
  }

  return (
    <div className="prod-chart">
      <ResponsiveContainer width="100%" height={Math.max(180, entries.length * 28)}>
        <BarChart
          data={entries}
          layout="vertical"
          margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
        >
          <CartesianGrid stroke="#22252e" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: "#9aa0ad", fontSize: 11 }}
            stroke="#3a3f4d"
            tickFormatter={(v) => formatMW(v)}
          />
          <YAxis
            type="category"
            dataKey="mode"
            tick={{ fill: "#cdd2db", fontSize: 12 }}
            stroke="#3a3f4d"
            width={120}
          />
          <Tooltip
            cursor={{ fill: "#2a2e38" }}
            contentStyle={{
              background: "#181b22",
              border: "1px solid #2c3140",
              borderRadius: 6,
              color: "#e7eaf0",
            }}
            formatter={(v: number) => [`${formatMW(v)}`, "Production"]}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {entries.map((e) => (
              <Cell key={e.mode} fill={getModeColor(e.mode)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function formatMW(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1)} GW`;
  return `${Math.round(value)} MW`;
}

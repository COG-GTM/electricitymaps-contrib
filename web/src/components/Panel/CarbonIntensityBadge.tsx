import { getCarbonIntensityColor } from "../../utils/colors";

interface Props {
  intensity: number | null | undefined;
  isEstimated?: boolean;
}

export function CarbonIntensityBadge({ intensity, isEstimated }: Props) {
  const display = intensity != null ? Math.round(intensity) : null;
  const color = getCarbonIntensityColor(intensity ?? null);

  return (
    <div className="ci-badge" style={{ backgroundColor: color }}>
      <div className="ci-badge__value">
        {display != null ? display : "—"}
        <span className="ci-badge__unit">gCO₂eq/kWh</span>
      </div>
      <div className="ci-badge__label">
        Carbon intensity{isEstimated ? " · estimated" : ""}
      </div>
    </div>
  );
}

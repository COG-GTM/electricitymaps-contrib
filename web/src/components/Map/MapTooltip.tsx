import { useAppContext } from "../../context/AppContext";

interface Props {
  zoneKey: string;
  intensity: number | null;
  x: number;
  y: number;
}

export function MapTooltip({ zoneKey, intensity, x, y }: Props) {
  const { zones } = useAppContext();
  const zone = zones?.[zoneKey];

  return (
    <div
      className="map-tooltip"
      style={{ transform: `translate(${x + 12}px, ${y + 12}px)` }}
    >
      <div className="map-tooltip__title">{zone?.zoneName ?? zoneKey}</div>
      <div className="map-tooltip__sub">{zoneKey}</div>
      <div className="map-tooltip__row">
        <span>Carbon intensity</span>
        <strong>
          {intensity != null ? `${Math.round(intensity)} gCO₂eq/kWh` : "no data"}
        </strong>
      </div>
    </div>
  );
}

import { Marker } from "react-map-gl/maplibre";

import { useAppContext } from "../../context/AppContext";

// Renders a static directional arrow at each cross-border interconnection
// indicated in exchanges.json. Magnitude/direction animation is left as a
// future enhancement once the backing dataset exposes flow values.
export function ExchangeArrows() {
  const { exchanges } = useAppContext();

  if (!exchanges) return null;

  return (
    <>
      {Object.entries(exchanges).map(([key, ex]) => {
        const [lon, lat] = ex.lonlat ?? [0, 0];
        if (lon === 0 && lat === 0) return null;
        return (
          <Marker
            key={key}
            longitude={lon}
            latitude={lat}
            rotation={ex.rotation ?? 0}
          >
            <ArrowGlyph />
          </Marker>
        );
      })}
    </>
  );
}

function ArrowGlyph() {
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 16 16"
      style={{ display: "block", pointerEvents: "none" }}
      aria-hidden
    >
      <path
        d="M8 1.5 L13.5 12 L8 9 L2.5 12 Z"
        fill="#f8fafc"
        stroke="#0c0c12"
        strokeWidth={1}
        strokeLinejoin="round"
      />
    </svg>
  );
}

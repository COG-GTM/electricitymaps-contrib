import { useMemo, useRef, useState, useEffect } from "react";
import Map, {
  Layer,
  Source,
  type MapMouseEvent,
  type MapRef,
} from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type {
  FillLayerSpecification,
  LineLayerSpecification,
} from "maplibre-gl";
import type { FeatureCollection } from "geojson";

import { useWorldGeo } from "../../hooks/useGeoJson";
import { useAppContext } from "../../context/AppContext";
import {
  CARBON_INTENSITY_COLORS,
  CARBON_INTENSITY_DOMAIN,
  NO_DATA_COLOR,
} from "../../utils/colors";
import { ExchangeArrows } from "./ExchangeArrows";
import { MapTooltip } from "./MapTooltip";

const ZONES_SOURCE = "zones";
const ZONES_FILL_LAYER = "zones-fill";
const ZONES_OUTLINE_LAYER = "zones-outline";
const ZONES_HOVER_LAYER = "zones-hover";

const INITIAL_VIEW = {
  longitude: 10,
  latitude: 30,
  zoom: 1.6,
};

interface HoverState {
  zoneKey: string;
  x: number;
  y: number;
}

export function ElectricityMap() {
  const mapRef = useRef<MapRef>(null);
  const worldGeo = useWorldGeo();
  const {
    selectedZone,
    setSelectedZone,
    getZoneIntensity,
    gridData,
    selectedDatetime,
  } = useAppContext();

  const [hover, setHover] = useState<HoverState | null>(null);

  // Build the geojson with each feature's carbon intensity as a property so
  // MapLibre can do data-driven styling without a separate join.
  const decoratedGeo = useMemo<FeatureCollection | null>(() => {
    if (!worldGeo.data) return null;
    const fc: FeatureCollection = {
      type: "FeatureCollection",
      features: worldGeo.data.features.map((f) => {
        const zoneKey =
          (f.properties as { zoneName?: string } | null)?.zoneName ?? "";
        const intensity = zoneKey ? getZoneIntensity(zoneKey) : null;
        return {
          ...f,
          id: zoneKey,
          properties: {
            ...(f.properties ?? {}),
            zoneKey,
            carbonIntensity: intensity ?? -1,
          },
        };
      }),
    };
    return fc;
    // We deliberately depend on the resolved time/grid so the layer reflects
    // the current slider position even though `getZoneIntensity` is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [worldGeo.data, gridData, selectedDatetime]);

  const fillLayer: FillLayerSpecification = {
    id: ZONES_FILL_LAYER,
    type: "fill",
    source: ZONES_SOURCE,
    paint: {
      "fill-color": [
        "case",
        ["<", ["get", "carbonIntensity"], 0],
        NO_DATA_COLOR,
        [
          "interpolate",
          ["linear"],
          ["get", "carbonIntensity"],
          ...CARBON_INTENSITY_DOMAIN.flatMap((stop, i) => [
            stop,
            CARBON_INTENSITY_COLORS[i],
          ]),
        ],
      ],
      "fill-opacity": 0.85,
    },
  };

  const outlineLayer: LineLayerSpecification = {
    id: ZONES_OUTLINE_LAYER,
    type: "line",
    source: ZONES_SOURCE,
    paint: {
      "line-color": "#0c0c12",
      "line-width": 0.4,
    },
  };

  const hoverLayer: LineLayerSpecification = {
    id: ZONES_HOVER_LAYER,
    type: "line",
    source: ZONES_SOURCE,
    paint: {
      "line-color": "#ffffff",
      "line-width": 2,
    },
    filter: ["==", ["get", "zoneKey"], hover?.zoneKey ?? "__none__"],
  };

  const handleMouseMove = (e: MapMouseEvent) => {
    const map = mapRef.current?.getMap();
    if (!map) return;
    const features = map.queryRenderedFeatures(e.point, {
      layers: [ZONES_FILL_LAYER],
    });
    const feat = features[0];
    if (feat) {
      const zoneKey =
        (feat.properties as { zoneKey?: string } | null)?.zoneKey ?? "";
      if (zoneKey) {
        setHover({ zoneKey, x: e.point.x, y: e.point.y });
        map.getCanvas().style.cursor = "pointer";
        return;
      }
    }
    setHover(null);
    map.getCanvas().style.cursor = "";
  };

  const handleMouseLeave = () => {
    setHover(null);
    const map = mapRef.current?.getMap();
    if (map) map.getCanvas().style.cursor = "";
  };

  const handleClick = (e: MapMouseEvent) => {
    const map = mapRef.current?.getMap();
    if (!map) return;
    const features = map.queryRenderedFeatures(e.point, {
      layers: [ZONES_FILL_LAYER],
    });
    const feat = features[0];
    if (feat) {
      const zoneKey =
        (feat.properties as { zoneKey?: string } | null)?.zoneKey ?? "";
      if (zoneKey) {
        setSelectedZone(zoneKey);
        return;
      }
    }
    if (selectedZone) setSelectedZone(null);
  };

  // Resize on mount in case the container animated in.
  useEffect(() => {
    const handle = setTimeout(() => mapRef.current?.resize(), 100);
    return () => clearTimeout(handle);
  }, []);

  return (
    <div className="map-root">
      <Map
        ref={mapRef}
        initialViewState={INITIAL_VIEW}
        mapStyle={EMPTY_STYLE}
        attributionControl={false}
        interactiveLayerIds={[ZONES_FILL_LAYER]}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        {decoratedGeo && (
          <Source id={ZONES_SOURCE} type="geojson" data={decoratedGeo}>
            <Layer {...fillLayer} />
            <Layer {...outlineLayer} />
            <Layer {...hoverLayer} />
          </Source>
        )}
        <ExchangeArrows />
      </Map>
      {hover && (
        <MapTooltip
          zoneKey={hover.zoneKey}
          intensity={getZoneIntensity(hover.zoneKey)}
          x={hover.x}
          y={hover.y}
        />
      )}
    </div>
  );
}

// A blank dark style — no external tile dependency keeps the demo offline-safe.
const EMPTY_STYLE = {
  version: 8 as const,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background" as const,
      paint: { "background-color": "#11141c" },
    },
  ],
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
};

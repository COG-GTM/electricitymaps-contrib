import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import type { ZoneMockData } from '../types';
import { getCO2Color, NO_DATA_COLOR } from '../colors';
import './MapView.css';

interface MapViewProps {
  mockData: Record<string, ZoneMockData>;
  selectedZone: string | null;
  onZoneSelect: (zoneKey: string | null) => void;
}

function buildGeoJsonWithColors(
  geojson: GeoJSON.FeatureCollection,
  data: Record<string, ZoneMockData>,
): GeoJSON.FeatureCollection {
  const hasData = Object.keys(data).length > 0;
  return {
    ...geojson,
    features: geojson.features.map((f) => {
      const zoneName = (f.properties as { zoneName?: string } | null)?.zoneName;
      const zd = hasData && zoneName ? data[zoneName] : undefined;
      return {
        ...f,
        properties: {
          ...(f.properties ?? {}),
          fillColor: zd ? getCO2Color(zd.carbonIntensity) : NO_DATA_COLOR,
          carbonIntensity: zd?.carbonIntensity ?? null,
        },
      };
    }),
  };
}

export default function MapView({
  mockData,
  selectedZone,
  onZoneSelect,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const geoJsonRef = useRef<GeoJSON.FeatureCollection | null>(null);
  const mapLoadedRef = useRef(false);
  const mockDataRef = useRef(mockData);
  mockDataRef.current = mockData;
  const onZoneSelectRef = useRef(onZoneSelect);
  onZoneSelectRef.current = onZoneSelect;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors',
          },
        },
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#1f2937',
            },
          },
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm-tiles',
            paint: {
              'raster-opacity': 0.25,
              'raster-saturation': -0.6,
              'raster-brightness-max': 0.85,
            },
          },
        ],
      },
      center: [10, 30],
      zoom: 2.2,
      minZoom: 1,
      maxZoom: 10,
    });

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      'top-right',
    );

    map.on('load', async () => {
      try {
        const resp = await fetch('/world.geojson');
        const geojson = (await resp.json()) as GeoJSON.FeatureCollection;
        geoJsonRef.current = geojson;

        const colored = buildGeoJsonWithColors(geojson, mockDataRef.current);

        map.addSource('zones', { type: 'geojson', data: colored });

        map.addLayer({
          id: 'zones-fill',
          type: 'fill',
          source: 'zones',
          paint: {
            'fill-color': ['get', 'fillColor'],
            'fill-opacity': 0.85,
          },
        });

        map.addLayer({
          id: 'zones-border',
          type: 'line',
          source: 'zones',
          paint: {
            'line-color': '#ffffff',
            'line-width': 0.6,
            'line-opacity': 0.5,
          },
        });

        map.addLayer({
          id: 'zones-highlight',
          type: 'line',
          source: 'zones',
          paint: {
            'line-color': '#0f172a',
            'line-width': 2.5,
            'line-opacity': 0,
          },
        });

        mapLoadedRef.current = true;
      } catch (err) {
        // Surface load errors via console; UI fallback is the gray map.
        console.error('Failed to load world.geojson:', err);
      }
    });

    map.on('click', 'zones-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const zone = (e.features[0].properties as { zoneName?: string } | null)
          ?.zoneName;
        if (zone) onZoneSelectRef.current(zone);
      }
    });

    map.on('mouseenter', 'zones-fill', () => {
      map.getCanvas().style.cursor = 'pointer';
    });

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 10,
      className: 'zone-popup',
    });

    map.on('mousemove', 'zones-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const props = e.features[0].properties as
          | {
              zoneName?: string;
              countryName?: string;
              carbonIntensity?: number | null;
            }
          | null;
        const zone = props?.zoneName;
        if (zone) {
          const ci = props?.carbonIntensity;
          const ciText =
            ci != null ? `${ci} gCO\u2082eq/kWh` : 'No data';

          const root = document.createElement('div');
          const title = document.createElement('div');
          title.className = 'zone-popup__title';
          title.textContent = props?.countryName ?? zone;
          const sub = document.createElement('div');
          sub.className = 'zone-popup__sub';
          sub.textContent = zone;
          const ciNode = document.createElement('div');
          ciNode.className = 'zone-popup__ci';
          ciNode.textContent = ciText;
          root.appendChild(title);
          root.appendChild(sub);
          root.appendChild(ciNode);

          popup.setLngLat(e.lngLat).setDOMContent(root).addTo(map);
        }
      }
    });

    map.on('mouseleave', 'zones-fill', () => {
      map.getCanvas().style.cursor = '';
      popup.remove();
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      mapLoadedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const geojson = geoJsonRef.current;
    if (
      !map ||
      !geojson ||
      !mapLoadedRef.current ||
      Object.keys(mockData).length === 0
    )
      return;

    const colored = buildGeoJsonWithColors(geojson, mockData);
    const source = map.getSource('zones') as
      | maplibregl.GeoJSONSource
      | undefined;
    if (source) source.setData(colored);
  }, [mockData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoadedRef.current) return;

    try {
      if (selectedZone) {
        map.setPaintProperty('zones-highlight', 'line-opacity', [
          'case',
          ['==', ['get', 'zoneName'], selectedZone],
          1,
          0,
        ] as unknown as maplibregl.ExpressionSpecification);
      } else {
        map.setPaintProperty('zones-highlight', 'line-opacity', 0);
      }
    } catch {
      // Layer may not be ready on the very first render.
    }
  }, [selectedZone]);

  return <div ref={containerRef} className="map-view" />;
}

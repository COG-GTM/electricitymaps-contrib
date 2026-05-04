export const CO2_COLOR_STOPS: [number, string][] = [
  [0, '#2AA364'],
  [150, '#F5EB4D'],
  [600, '#9E4229'],
  [800, '#381D02'],
  [1500, '#000000'],
];

function interpolateColor(c1: string, c2: string, t: number): string {
  const r1 = parseInt(c1.slice(1, 3), 16);
  const g1 = parseInt(c1.slice(3, 5), 16);
  const b1 = parseInt(c1.slice(5, 7), 16);
  const r2 = parseInt(c2.slice(1, 3), 16);
  const g2 = parseInt(c2.slice(3, 5), 16);
  const b2 = parseInt(c2.slice(5, 7), 16);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

export function getCO2Color(intensity: number): string {
  if (intensity <= 0) return CO2_COLOR_STOPS[0][1];
  if (intensity >= 1500) return CO2_COLOR_STOPS[CO2_COLOR_STOPS.length - 1][1];

  for (let i = 1; i < CO2_COLOR_STOPS.length; i++) {
    const [prevVal, prevColor] = CO2_COLOR_STOPS[i - 1];
    const [nextVal, nextColor] = CO2_COLOR_STOPS[i];
    if (intensity <= nextVal) {
      const t = (intensity - prevVal) / (nextVal - prevVal);
      return interpolateColor(prevColor, nextColor, t);
    }
  }
  return CO2_COLOR_STOPS[CO2_COLOR_STOPS.length - 1][1];
}

export const CO2_GRADIENT_CSS =
  'linear-gradient(to right, #2AA364 0%, #F5EB4D 10%, #9E4229 40%, #381D02 53%, #000000 100%)';

export const MODE_COLORS: Record<string, string> = {
  nuclear: '#AE4BBD',
  wind: '#74cdb9',
  solar: '#f27406',
  hydro: '#2772b2',
  'hydro storage': '#1B5E8C',
  'hydro discharge': '#3D8EB9',
  'battery storage': '#B76ECD',
  'battery discharge': '#9B4DCA',
  gas: '#bb2f51',
  coal: '#ac8c35',
  oil: '#867d66',
  biomass: '#A1A422',
  geothermal: '#CD6340',
  'unknown fossil': '#666666',
  'unknown renewable': '#8BC34A',
  unknown: '#ACACAC',
};

export const NO_DATA_COLOR = '#d4d4d4';

// Bottom-to-top render order for stacked electricity-mix area charts.
export const MIX_RENDER_ORDER: string[] = [
  'nuclear',
  'hydro',
  'hydro storage',
  'hydro discharge',
  'battery discharge',
  'wind',
  'solar',
  'geothermal',
  'biomass',
  'gas',
  'oil',
  'coal',
  'unknown',
  'unknown renewable',
  'unknown fossil',
  'battery storage',
];

export function modeColor(mode: string): string {
  return MODE_COLORS[mode] ?? MODE_COLORS.unknown;
}

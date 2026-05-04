import './CarbonLegend.css';

export default function CarbonLegend() {
  return (
    <div className="carbon-legend">
      <div className="carbon-legend__header">
        <span className="carbon-legend__title">Carbon intensity</span>
        <span className="carbon-legend__unit">gCO&#x2082;eq/kWh</span>
      </div>
      <div className="carbon-legend__bar" />
      <div className="carbon-legend__ticks">
        <span>0</span>
        <span>300</span>
        <span>600</span>
        <span>900</span>
        <span>1200</span>
        <span>1500</span>
      </div>
    </div>
  );
}

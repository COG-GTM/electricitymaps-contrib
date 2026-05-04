import { AppProvider, useAppContext } from "./context/AppContext";
import { ElectricityMap } from "./components/Map/ElectricityMap";
import { ZonePanel } from "./components/Panel/ZonePanel";
import { ColorLegend } from "./components/Legend/ColorLegend";
import { TimeSlider } from "./components/BottomBar/TimeSlider";

function AppShell() {
  const { loading, error } = useAppContext();

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__brand">
          <span className="app__logo" aria-hidden>⚡</span>
          <span className="app__title">Electricity Maps</span>
        </div>
        <div className="app__sub">
          Live grid carbon intensity by zone — built on COG-GTM/electricitymaps-contrib.
        </div>
      </header>

      <div className="app__main">
        <ElectricityMap />
        <ZonePanel />
        <ColorLegend />
      </div>

      <div className="app__footer">
        <TimeSlider />
      </div>

      {loading && (
        <div className="app__overlay" role="status" aria-live="polite">
          Loading grid data…
        </div>
      )}
      {error && !loading && (
        <div className="app__overlay app__overlay--error" role="alert">
          Failed to load data: {error.message}
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}

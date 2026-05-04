import { useAppContext } from "../../context/AppContext";

export function TimeSlider() {
  const { datetimes, selectedDatetime, setSelectedDatetime } = useAppContext();

  if (datetimes.length === 0) return null;

  const idx = selectedDatetime
    ? Math.max(0, datetimes.indexOf(selectedDatetime))
    : datetimes.length - 1;

  const current = datetimes[idx] ?? datetimes[datetimes.length - 1];

  return (
    <div className="time-slider" role="group" aria-label="Time slider">
      <div className="time-slider__row">
        <button
          type="button"
          className="time-slider__btn"
          aria-label="Previous timestep"
          disabled={idx === 0}
          onClick={() => setSelectedDatetime(datetimes[Math.max(0, idx - 1)])}
        >
          ‹
        </button>

        <div className="time-slider__label">
          <div className="time-slider__time">{formatDt(current)}</div>
          <div className="time-slider__hint">
            {idx + 1} / {datetimes.length}
          </div>
        </div>

        <button
          type="button"
          className="time-slider__btn"
          aria-label="Next timestep"
          disabled={idx === datetimes.length - 1}
          onClick={() =>
            setSelectedDatetime(datetimes[Math.min(datetimes.length - 1, idx + 1)])
          }
        >
          ›
        </button>
      </div>
      <input
        type="range"
        min={0}
        max={datetimes.length - 1}
        step={1}
        value={idx}
        onChange={(e) => setSelectedDatetime(datetimes[Number(e.target.value)])}
        className="time-slider__range"
        aria-label="Scrub through time"
      />
    </div>
  );
}

function formatDt(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return iso;
  }
}

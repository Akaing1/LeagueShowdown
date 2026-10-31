import { useEffect, useState } from "react";

export function FullscreenButton() {
  const [active, setActive] = useState(Boolean(document.fullscreenElement));
  const [error, setError] = useState("");
  useEffect(() => {
    const sync = () => setActive(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", sync);
    return () => document.removeEventListener("fullscreenchange", sync);
  }, []);
  async function toggle() {
    setError("");
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      setError(
        "Fullscreen could not open. Try your browser's fullscreen option.",
      );
    }
  }
  return (
    <div className="fullscreen-control">
      <button
        type="button"
        className="quiet"
        aria-pressed={active}
        disabled={!document.fullscreenEnabled}
        title={
          document.fullscreenEnabled
            ? "Toggle fullscreen (Escape to exit)"
            : "Use your browser's fullscreen option"
        }
        onClick={() => void toggle()}
      >
        {active ? "Exit fullscreen" : "Fullscreen"}
      </button>
      {error && <span role="alert">{error}</span>}
    </div>
  );
}

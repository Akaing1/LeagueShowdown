import { useEffect, useState } from "react";
import type { Show } from "../../types/show";

export function SplashArt({ s, offset }: { s: Show; offset: number }) {
  const [, redraw] = useState(0);
  const now = Date.now();
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let frame: number;
    const tick = () => {
      redraw((value) => value + 1);
      frame = requestAnimationFrame(tick);
    };
    if (s.round_deadline && !s.paused) frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [s.round_deadline, s.paused]);
  const remaining =
    s.round_deadline && !s.paused
      ? Math.max(0, s.round_deadline - (now + offset) / 1000)
      : (s.round_remaining ?? 30);
  const scale =
    s.phase === "revealed" ? 1 : 1 + (11 * Math.min(30, remaining)) / 30;
  const [x, y] = s.crop ?? [0.5, 0.5];
  return (
    <div className="splash-art">
      <div
        className="splash-frame"
        role="img"
        aria-label="Mystery champion splash art"
      >
        {!loaded && !failed && (
          <p className="splash-message" role="status">
            Loading splash art…
          </p>
        )}
        {failed ? (
          <div className="splash-message" role="alert">
            <p>Splash art could not load.</p>
            <button
              onClick={() => {
                setFailed(false);
                setLoaded(false);
              }}
            >
              Retry image
            </button>
          </div>
        ) : (
          <img
            src={s.splash_url ?? ""}
            alt=""
            draggable={false}
            onLoad={() => setLoaded(true)}
            onError={() => setFailed(true)}
            style={{
              visibility: loaded ? "visible" : "hidden",
              transform: `translate(${(0.5 - x) * (scale - 1) * 100}%, ${(0.5 - y) * (scale - 1) * 100}%) scale(${scale})`,
            }}
          />
        )}
      </div>
      <p className="muted small">
        {s.phase === "revealed"
          ? "The full picture."
          : s.paused
            ? "Zoom paused."
            : ["answering", "judging"].includes(s.phase)
              ? "Zoom paused while a contestant answers. You can still join the buzzer queue."
              : remaining <= 0
                ? "Full splash revealed. Buzz in if you know the champion!"
                : "Watch closely. Buzz in to freeze the zoom."}
      </p>
    </div>
  );
}

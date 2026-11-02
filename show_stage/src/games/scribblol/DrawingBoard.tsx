import { useRef, useState, useEffect } from "react";
import type { Show, Act, Stroke } from "../../types/show";

const path = (points: number[][]) =>
  points.map(([x, y], i) => `${i ? "L" : "M"}${x * 800},${y * 450}`).join(" ");
export function DrawingBoard({
  s,
  act,
  disabled,
}: {
  s: Show;
  act: Act;
  disabled: boolean;
}) {
  const [color, setColor] = useState("#172d39");
  const [width, setWidth] = useState(6);
  const [draft, setDraft] = useState<Stroke | null>(null);
  const stroke = useRef<Stroke | null>(null);
  const artist = s.players.find((p) => p.id === s.artist);
  const canDraw =
    s.you === s.artist && s.phase === "open" && !s.paused && !disabled;
  useEffect(() => {
    stroke.current = null;
    setDraft(null);
  }, [s.index, s.phase, s.paused]);
  function point(e: React.PointerEvent<SVGSVGElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    return [
      Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)),
      Math.max(0, Math.min(1, (e.clientY - r.top) / r.height)),
    ];
  }
  return (
    <div className="drawing-game">
      <p className="eyebrow">{artist?.name} is drawing</p>
      {s.you === s.artist && (
        <div className="artist-prompt">
          <strong>Your ability: {s.answer}</strong>
          <p>Draw without letters or numbers. You cannot buzz in.</p>
        </div>
      )}
      {s.you === s.artist && (
        <div className="drawing-tools">
          <div className="ink-palette" role="group" aria-label="Ink color">
            {[
              ["Black", "#172d39"],
              ["Red", "#e74c3c"],
              ["Blue", "#2e86de"],
              ["Green", "#27ae60"],
              ["Yellow", "#f1c40f"],
            ].map(([name, value]) => (
              <button
                key={value}
                type="button"
                className="ink-swatch"
                style={{ backgroundColor: value }}
                aria-label={name}
                title={name}
                aria-pressed={color === value}
                disabled={!canDraw}
                onClick={() => setColor(value)}
              >
                {color === value && <span aria-hidden="true">✓</span>}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="eraser-tool"
            aria-pressed={color === "#ffffff"}
            disabled={!canDraw}
            onClick={() => setColor("#ffffff")}
          >
            Eraser
          </button>
          <label className="brush-slider">
            <span>
              Brush size <output aria-hidden="true">{width}px</output>
            </span>
            <input
              type="range"
              aria-label="Brush size"
              aria-valuetext={`${width} pixels`}
              min={3}
              max={24}
              step={1}
              value={width}
              disabled={!canDraw}
              onChange={(e) => setWidth(Number(e.target.value))}
            />
          </label>
          <button
            disabled={!canDraw || !s.strokes?.length}
            onClick={() =>
              void act("erase_stroke", { question_index: s.index })
            }
          >
            Undo stroke
          </button>
          <button
            disabled={!canDraw || !s.strokes?.length}
            onClick={() =>
              void act("clear_canvas", { question_index: s.index })
            }
          >
            Clear canvas
          </button>
        </div>
      )}
      <svg
        className={`drawing-canvas ${canDraw ? "editable" : ""}`}
        viewBox="0 0 800 450"
        preserveAspectRatio="none"
        role="img"
        aria-label="Shared drawing canvas"
        onPointerDown={(e) => {
          if (!canDraw || stroke.current) return;
          e.preventDefault();
          e.currentTarget.setPointerCapture(e.pointerId);
          const next = { color, width, points: [point(e)] };
          stroke.current = next;
          setDraft(next);
        }}
        onPointerMove={(e) => {
          if (!stroke.current || !canDraw) return;
          const points = [...stroke.current.points];
          if (points.length < 128) points.push(point(e));
          else points[127] = point(e);
          stroke.current = { ...stroke.current, points };
          setDraft(stroke.current);
        }}
        onPointerUp={(e) => {
          const next = stroke.current;
          stroke.current = null;
          if (e.currentTarget.hasPointerCapture(e.pointerId))
            e.currentTarget.releasePointerCapture(e.pointerId);
          if (next && canDraw)
            void act("draw", { ...next, question_index: s.index }).finally(() =>
              setDraft(null),
            );
          else setDraft(null);
        }}
        onPointerCancel={() => {
          stroke.current = null;
          setDraft(null);
        }}
      >
        {[...(s.strokes ?? []), ...(draft ? [draft] : [])].map((line, i) =>
          line.points.length === 1 ? (
            <circle
              key={i}
              cx={line.points[0][0] * 800}
              cy={line.points[0][1] * 450}
              r={line.width / 2}
              fill={line.color}
            />
          ) : (
            <path
              key={i}
              d={path(line.points)}
              fill="none"
              stroke={line.color}
              strokeWidth={line.width}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ),
        )}
      </svg>
      {s.you === s.artist && s.phase !== "revealed" && (
        <p className="muted small">
          {s.paused
            ? "Show paused."
            : s.phase !== "open"
              ? "Drawing pauses while a contestant answers."
              : "Use your mouse, pen, or touch to draw the ability."}
        </p>
      )}
    </div>
  );
}

import { useState } from "react";
import type { Show, Act } from "../../types/show";

export function HostControls({
  s,
  disabled,
  act,
}: {
  s: Show;
  disabled: boolean;
  act: Act;
}) {
  const [copied, setCopied] = useState("");
  const [adjustPlayer, setAdjustPlayer] = useState("0");
  const [adjustPoints, setAdjustPoints] = useState("100");
  const room = s.room_id;
  const activePlayer = s.players.find((p) => p.id === s.active);
  async function copyLink(label: string, path: string) {
    try {
      await navigator.clipboard.writeText(`${location.origin}${path}`);
      setCopied(label);
    } catch {
      setCopied("Copy the link from its text field.");
    }
  }

  return (
    <aside className="host-controls">
      <section className="panel">
        <div className="panel-heading">
          <h2>Round controls</h2>
          <span className="tag">HOST ONLY</span>
        </div>
        <div className="host-answer">
          <span className="eyebrow">ANSWER KEY</span>
          <strong>{s.answer || "Start to see the first champion"}</strong>
          {s.all_hints?.map((hint, i) => (
            <p key={i} className={i < s.revealed ? "muted" : ""}>
              {i + 1}. {hint}
            </p>
          ))}
        </div>
        {s.submission && (
          <div className="submitted">
            <span className="eyebrow">{activePlayer?.name}'S ANSWER</span>
            <strong>{s.submission}</strong>
          </div>
        )}
        <div className="control-buttons">
          {s.phase === "lobby" && (
            <button
              className="primary"
              disabled={disabled}
              onClick={() => void act("start")}
            >
              Start Who Am I? →
            </button>
          )}
          {s.phase === "revealed" && (
            <button
              className="primary"
              disabled={disabled || s.paused}
              onClick={() => void act("next")}
            >
              {s.index + 1 === s.total ? "Finish showdown" : "Next champion →"}
            </button>
          )}
          {["clue", "open"].includes(s.phase) && (
            <>
              <button
                className="primary"
                disabled={
                  disabled ||
                  s.paused ||
                  s.phase !== "clue" ||
                  s.locked.length === 3
                }
                onClick={() => void act("open")}
              >
                Open buzzers
              </button>
              <button
                disabled={disabled || s.paused || s.revealed === s.hint_count}
                onClick={() => void act("hint")}
              >
                Reveal next clue
              </button>
              <button
                className="quiet"
                disabled={disabled || s.paused}
                onClick={() => void act("reveal")}
              >
                Reveal answer / skip
              </button>
            </>
          )}
          {["answering", "judging"].includes(s.phase) && (
            <div className="judge-buttons">
              <button
                className="success"
                disabled={disabled || s.paused}
                onClick={() => void act("judge", { correct: true })}
              >
                ✓ Correct
              </button>
              <button
                className="danger"
                disabled={disabled || s.paused}
                onClick={() => void act("judge", { correct: false })}
              >
                ✕ Incorrect
              </button>
            </div>
          )}
          {!["lobby", "finished"].includes(s.phase) && (
            <button
              disabled={disabled}
              onClick={() => void act(s.paused ? "resume" : "pause")}
            >
              {s.paused ? "Resume show" : "Pause show"}
            </button>
          )}
          <button
            className="quiet"
            disabled={disabled || !s.can_undo}
            onClick={() => void act("undo")}
          >
            ↶ Undo last action
          </button>
        </div>
      </section>
      <details className="panel">
        <summary>Contestant & broadcast links</summary>
        <p className="muted small">
          Keep contestant links private. Share the broadcast link with OBS.
        </p>
        {s.invites?.map((token, i) => (
          <div className="invite" key={i}>
            <label>
              {s.players[i].name}
              <input
                readOnly
                value={`${location.origin}/play/${room}#${token}`}
                onFocus={(e) => e.target.select()}
              />
            </label>
            <button
              onClick={() =>
                void copyLink(s.players[i].name, `/play/${room}#${token}`)
              }
            >
              Copy
            </button>
          </div>
        ))}
        <a
          className="text-link"
          href={`/show/${room}`}
          target="_blank"
          rel="noreferrer"
        >
          Open broadcast view ↗
        </a>
        <button
          className="quiet"
          onClick={() => void copyLink("Broadcast", `/show/${room}`)}
        >
          Copy broadcast link
        </button>
        {copied && (
          <p role="status" className="small">
            {copied.includes("Copy the") ? copied : `${copied} link copied`}
          </p>
        )}
      </details>
      <details className="panel">
        <summary>Adjust a score</summary>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void act("adjust", {
              player: adjustPlayer,
              points: Number(adjustPoints),
            });
          }}
        >
          <label>
            Contestant
            <select
              value={adjustPlayer}
              onChange={(e) => setAdjustPlayer(e.target.value)}
            >
              {s.players.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Points to add or subtract
            <input
              type="number"
              min={-10000}
              max={10000}
              required
              value={adjustPoints}
              onChange={(e) => setAdjustPoints(e.target.value)}
            />
          </label>
          <button disabled={disabled || s.paused}>Apply adjustment</button>
        </form>
      </details>
    </aside>
  );
}

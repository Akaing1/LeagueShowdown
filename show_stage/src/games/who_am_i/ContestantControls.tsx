import { useEffect, useState } from "react";
import type { Show, Act } from "../../types/show";
export function ContestantControls({
  s,
  disabled,
  act,
  phaseLabel,
}: {
  s: Show;
  disabled: boolean;
  act: Act;
  phaseLabel: string;
}) {
  const [answer, setAnswer] = useState("");
  useEffect(() => {
    setAnswer("");
  }, [s.index, s.active]);
  const queuePosition = (s.queue ?? []).indexOf(s.you);
  const canBuzz =
    ["open", "answering", "judging"].includes(s.phase) &&
    !s.paused &&
    !s.locked.includes(s.you) &&
    queuePosition < 0 &&
    s.active !== s.you;
  return (
    <div className="player-actions">
      {s.active === s.you && ["answering", "judging"].includes(s.phase) ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void act("submit_answer", { answer });
          }}
        >
          <label>
            Your answer
            <input
              autoFocus
              maxLength={120}
              disabled={s.phase === "judging" || s.paused}
              value={s.submission || answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Champion name"
            />
          </label>
          <button
            className="primary"
            disabled={
              disabled || s.phase !== "answering" || s.paused || !answer.trim()
            }
          >
            {s.phase === "judging"
              ? "Answer locked · awaiting host"
              : "Lock in answer"}
          </button>
          <p className="muted small">
            You can also answer aloud for your host to judge.
          </p>
        </form>
      ) : (
        <>
          <button
            className="buzz"
            disabled={disabled || !canBuzz}
            onClick={() => void act("buzz")}
          >
            {s.locked.includes(s.you)
              ? "Wait for the next question"
              : queuePosition >= 0
                ? `Queued · ${queuePosition + 1} in line`
                : canBuzz
                  ? "BUZZ IN"
                  : "Stand by"}
          </button>
          <p className="muted small">
            {queuePosition >= 0
              ? "You will answer if the contestants ahead miss."
              : canBuzz
                ? s.active
                  ? "Buzz to join the queue."
                  : "Click to claim your answer."
                : phaseLabel}
          </p>
        </>
      )}
    </div>
  );
}

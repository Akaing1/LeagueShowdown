import { DrawingBoard } from "../games/scribblol/DrawingBoard";
import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Header } from "../components/layout/Header";
import { FullscreenButton } from "../components/controls/FullscreenButton";
import { Scoreboard } from "../components/show/Scoreboard";
import { ConnectionStatus } from "../components/show/ConnectionStatus";
import { ClueCards } from "../games/who_am_i/ClueCards";
import { HostControls } from "../components/show/HostControls";
import { ContestantControls } from "../components/show/ContestantControls";
import { useShow } from "../hooks/useShow";
import { useClock } from "../hooks/useClock";
export function ShowPage({ mode }: { mode: "host" | "play" | "show" }) {
  const { room = "" } = useParams();
  const navigate = useNavigate();
  const { state: s, connected, error, busy, act, offset } = useShow(room, mode);
  const now = useClock();
  useEffect(() => {
    if (mode === "host" && s && s.you !== "host") navigate("/");
  }, [mode, s, navigate]);
  if (!s)
    return (
      <>
        <Header />
        <main className="empty">
          <h1>{error ? "Unable to join" : "Entering the Rift…"}</h1>
          <p role={error ? "alert" : undefined}>
            {error || "Connecting to your showdown."}
          </p>
          <Link to="/">Back to home</Link>
        </main>
      </>
    );
  const drawing = s.game_type === "scribblol";
  const drawingSeconds = s.round_deadline
    ? Math.max(0, Math.ceil(s.round_deadline - (now + offset.current) / 1000))
    : Math.ceil(s.round_remaining ?? 90);
  const host = mode === "host" && s.you === "host";
  const player = s.players.find((p) => p.id === s.you);
  const activePlayer = s.players.find((p) => p.id === s.active);
  const seconds = s.paused
    ? Math.ceil(s.remaining ?? 0)
    : s.deadline
      ? Math.max(0, Math.ceil(s.deadline - (now + offset.current) / 1000))
      : null;
  const disabled = busy || !connected;
  const phaseLabel = s.paused
    ? "Show paused"
    : {
        lobby: "Waiting for the host",
        clue: "Buzzers closed",
        open: "Buzzers open",
        answering: `${activePlayer?.name} is answering`,
        judging: "Host is judging",
        revealed: "Answer revealed",
        finished: "Show complete",
      }[s.phase] || s.phase;
  return (
    <div className={`show-page ${mode}`}>
      <Header>
        <FullscreenButton />
        <ConnectionStatus connected={connected} />
      </Header>
      <main className="arena">
        <div className="show-title">
          <div>
            <div className="eyebrow">
              {host
                ? "HOST CONSOLE"
                : player
                  ? `CONTESTANT · ${player.name}`
                  : "RATS ON THE RIFT"}
            </div>
            <h1>{drawing ? "ScribbLoL" : "Who Am I?"}</h1>
          </div>
          <div className="round-label">
            {s.phase === "lobby"
              ? "READY WHEN YOU ARE"
              : `QUESTION ${s.index + 1} / ${s.total}`}
            <strong>
              {s.phase === "lobby"
                ? "The stage is set."
                : `${s.points} points at stake`}
            </strong>
          </div>
        </div>
        <div className="game-layout">
          <div className="stage-column">
            <section className="stage panel">
              <div className="stage-top">
                <span
                  className={`status ${s.phase === "open" && !s.paused ? "open" : ""}`}
                >
                  {phaseLabel}
                </span>
                {drawing &&
                  !["lobby", "finished", "revealed"].includes(s.phase) && (
                    <span className="drawing-time">
                      Drawing: {drawingSeconds}s
                    </span>
                  )}
                {seconds !== null && (
                  <span className="timer" role="timer">
                    {seconds}s
                  </span>
                )}
              </div>
              {s.phase === "lobby" ? (
                <div className="intro">
                  <div className="mystery">?</div>
                  <h2>
                    {drawing
                      ? "Draw the ability. Claim the points."
                      : "Know your champions?"}
                  </h2>
                  <p>
                    {drawing
                      ? "Six rounds. Two turns drawing each."
                      : "Four clues. Three contestants. One answer."}
                  </p>
                  <p className="muted">
                    {drawing
                      ? "Artist and first correct guesser earn 200 each. Nobody correct? Artist loses 100."
                      : `Guess early for more points. A wrong answer costs ${s.wrong_penalty} points.`}
                  </p>
                </div>
              ) : s.phase === "finished" ? (
                <div className="intro">
                  <div className="eyebrow">THE FINAL STANDINGS</div>
                  <h2>
                    {s.players
                      .filter(
                        (p) =>
                          p.score ===
                          Math.max(...s.players.map((p) => p.score)),
                      )
                      .map((p) => p.name)
                      .join(" & ")}
                  </h2>
                  <p>
                    {s.players.filter(
                      (p) =>
                        p.score === Math.max(...s.players.map((p) => p.score)),
                    ).length > 1
                      ? "share the lead — a tie!"
                      : "wins the showdown!"}
                  </p>
                </div>
              ) : drawing ? (
                <DrawingBoard s={s} act={act} disabled={disabled} />
              ) : (
                <ClueCards s={s} />
              )}
              {s.phase === "revealed" && (
                <div className="answer-reveal">
                  <div className="eyebrow">
                    {drawing ? "THE ABILITY IS" : "THE CHAMPION IS"}
                  </div>
                  <h2>{s.answer}</h2>
                </div>
              )}
              {s.last_result && (
                <div
                  className={`result ${s.last_result.correct ? "correct" : "incorrect"}`}
                  aria-live="polite"
                >
                  <strong>
                    {s.last_result.player} ·{" "}
                    {s.last_result.points > 0 ? "+" : ""}
                    {s.last_result.points}
                  </strong>
                  <span>{s.last_result.reason}</span>
                </div>
              )}
              {mode === "play" && player && s.you !== s.artist && (
                <ContestantControls
                  s={s}
                  disabled={disabled}
                  act={act}
                  phaseLabel={phaseLabel}
                />
              )}
            </section>
            <Scoreboard s={s} seconds={seconds} />
          </div>
          {host && <HostControls s={s} disabled={disabled} act={act} />}
        </div>

        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <footer>
          <span>
            {host
              ? "Host decisions are final. Undo pauses the restored round."
              : `${drawing ? "SCRIBBLOL" : "WHO AM I?"} · LEAGUE OF LEGENDS`}
          </span>
          <span>{drawing ? "04" : "01"} / 04 GAMES</span>
        </footer>
      </main>
    </div>
  );
}

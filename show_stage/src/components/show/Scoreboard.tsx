import type { Show } from "../../types/show";
export function Scoreboard({
  s,
  seconds,
}: {
  s: Show;
  seconds?: number | null;
}) {
  return (
    <section className="scoreboard" aria-label="Contestant scores">
      {s.players.map((p, i) => (
        <div
          key={p.id}
          className={`score-card player-${i} ${s.active === p.id ? "active" : ""} ${s.you === p.id ? "you" : ""}`}
        >
          <div className="player-number">0{i + 1}</div>
          <div className="player-info">
            <strong>{p.name}</strong>
            <span>
              {s.active === p.id
                ? s.phase === "judging"
                  ? "ANSWER LOCKED"
                  : `ANSWERING${seconds != null ? ` · ${seconds}s` : ""}`
                : s.artist === p.id
                  ? "ARTIST"
                  : (s.queue ?? []).includes(p.id)
                    ? `QUEUED · ${(s.queue ?? []).indexOf(p.id) + 1}`
                    : s.locked.includes(p.id)
                      ? "LOCKED UNTIL NEXT QUESTION"
                      : s.online.includes(p.id)
                        ? "CONNECTED"
                        : "DISCONNECTED"}
            </span>
          </div>
          <div className="score">
            {p.score}
            <span>POINTS</span>
          </div>
        </div>
      ))}
    </section>
  );
}

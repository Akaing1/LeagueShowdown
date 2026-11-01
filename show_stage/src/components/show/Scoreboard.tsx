import type { Show } from "../../types/show";
export function Scoreboard({ s }: { s: Show }) {
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
                ? "ANSWERING"
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

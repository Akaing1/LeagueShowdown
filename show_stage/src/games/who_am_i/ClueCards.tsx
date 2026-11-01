import type { Show } from "../../types/show";
export function ClueCards({ s }: { s: Show }) {
  return (
    <div className="clues">
      <div className="eyebrow">IDENTIFY THE CHAMPION</div>
      {Array.from({ length: s.hint_count }, (_, i) => (
        <div
          key={`${s.index}-${i}-${i < s.hints.length}`}
          className={`clue ${i >= s.hints.length ? "concealed" : "clue-revealed"}`}
        >
          <span className="clue-number">0{i + 1}</span>
          <p>{s.hints[i] || "Clue not yet revealed"}</p>
        </div>
      ))}
    </div>
  );
}

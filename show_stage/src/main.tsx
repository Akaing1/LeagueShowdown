import { StrictMode, useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import "./style.css";
import { FullscreenButton } from "./FullscreenButton";

type Player = { id: string; name: string; score: number };
type Show = {
  room_id: string;
  revision: number;
  you: string;
  players: Player[];
  phase: string;
  index: number;
  total: number;
  hints: string[];
  hint_count: number;
  revealed: number;
  points: number;
  wrong_penalty: number;
  active: string | null;
  locked: string[];
  deadline: number | null;
  paused: boolean;
  remaining: number | null;
  answer?: string;
  all_hints?: string[];
  submission?: string | null;
  invites?: string[];
  can_undo?: boolean;
  online: string[];
  server_time: number;
  last_result: {
    player: string;
    correct: boolean;
    points: number;
    reason: string;
  } | null;
};
type Room = { id: string; names: string[]; phase: string };

async function api(path: string, options: RequestInit = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
    signal: AbortSignal.timeout(10000),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check your entries.",
    );
  return data;
}

function Brand() {
  return (
    <Link to="/" className="brand">
      <span className="crest">R</span>
      <span className="brand-copy">
        <span>
          RATS ON <b>THE RIFT</b>
        </span>
        <span className="edition">LEAGUE OF LEGENDS EDITION</span>
      </span>
    </Link>
  );
}
function Header({ children }: { children?: React.ReactNode }) {
  return (
    <header>
      <Brand />
      <div className="header-right">{children}</div>
    </header>
  );
}

function Lobby() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState<Room[] | null>(null);
  const [password, setPassword] = useState("");
  const [names, setNames] = useState(["", "", ""]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api("/rooms")
      .then(setRooms)
      .catch(() => setRooms(null));
  }, []);
  async function login(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      setPassword("");
      setRooms(await api("/rooms"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function create(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const room: Show = await api("/rooms", {
        method: "POST",
        body: JSON.stringify({ names }),
      });
      navigate(`/host/${room.room_id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Header>
        {rooms && (
          <button
            className="quiet"
            onClick={async () => {
              await api("/logout", { method: "POST" });
              setRooms(null);
            }}
          >
            Sign out
          </button>
        )}
      </Header>
      <main className="lobby">
        <div className="eyebrow">THREE CONTESTANTS. ONE RIFT.</div>
        <h1>
          A battle of
          <br />
          <em>League knowledge.</em>
        </h1>
        <p className="lede">
          Clues, quick thinking, and a little calculated risk.
          <br />
          Your next showdown starts here.
        </p>
        <div className="lineup">
          <span className="selected">01 · Who Am I?</span>
          <span>02 · Splash Zone</span>
          <span>03 · EmoGG</span>
          <span>04 · ScribbLoL</span>
        </div>
        <section className="panel setup">
          <div className="panel-heading">
            <h2>{rooms ? "Set the stage" : "Host sign in"}</h2>
            <span className="tag">WHO AM I?</span>
          </div>
          {rooms ? (
            <form onSubmit={create}>
              <p className="muted">
                Name your three contestants. Each gets their own private link.
              </p>
              <div className="name-fields">
                {names.map((name, i) => (
                  <label key={i}>
                    Contestant {i + 1}
                    <input
                      required
                      maxLength={32}
                      value={name}
                      placeholder={
                        ["The strategist", "The wildcard", "The dark horse"][i]
                      }
                      onChange={(e) =>
                        setNames(
                          names.map((n, j) => (j === i ? e.target.value : n)),
                        )
                      }
                    />
                  </label>
                ))}
              </div>
              <button className="primary" disabled={busy}>
                Create showdown <span>→</span>
              </button>
            </form>
          ) : (
            <form onSubmit={login}>
              <label>
                Host password
                <input
                  autoComplete="current-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <button className="primary" disabled={busy}>
                Enter host console →
              </button>
              <p className="muted small">
                Contestants: use the private link provided by your host.
              </p>
            </form>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>
        {rooms && rooms.length > 0 && (
          <section className="saved">
            <h2>Resume a showdown</h2>
            {rooms.map((room) => (
              <Link key={room.id} to={`/host/${room.id}`}>
                <span>{room.names.join(" / ")}</span>
                <span className="tag">{room.phase} →</span>
              </Link>
            ))}
          </section>
        )}
        <p className="footnote">
          Who Am I? is playable. The other three games are planned.
        </p>
      </main>
    </>
  );
}

function useShow(room: string, mode: string) {
  const [state, setState] = useState<Show | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const token = useRef("");
  const revision = useRef(-1);
  const offset = useRef(0);
  const receive = useCallback((next: Show) => {
    if (next.revision < revision.current) return;
    revision.current = next.revision;
    offset.current = next.server_time * 1000 - Date.now();
    setState(next);
  }, []);
  useEffect(() => {
    revision.current = -1;
    setState(null);
    setError("");
    if (mode === "play") {
      const key = `showdown-seat:${room}`;
      if (window.location.hash) {
        token.current = window.location.hash.slice(1);
        sessionStorage.setItem(key, token.current);
        history.replaceState(null, "", window.location.pathname);
      } else token.current = sessionStorage.getItem(key) || "";
      if (!token.current) {
        setError(
          "This contestant link is missing its private key. Ask your host for the full link.",
        );
        return;
      }
    } else token.current = "";
    let disposed = false;
    let socket: WebSocket;
    let retry: ReturnType<typeof setTimeout>;
    let delay = 1000;
    const headers =
      mode === "show"
        ? { "X-Showdown-View": "audience" }
        : token.current
          ? { Authorization: `Bearer ${token.current}` }
          : {};
    api(`/rooms/${room}`, { headers: headers as Record<string, string> })
      .then((next) => {
        if (!disposed) receive(next);
      })
      .catch((e) => {
        if (!disposed) setError(e.message);
      });
    function connect() {
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/rooms/${room}/live`,
      );
      socket.onopen = () =>
        socket.send(
          JSON.stringify({
            token: token.current,
            view: mode === "show" ? "audience" : mode,
          }),
        );
      socket.onmessage = (event) => {
        const next = JSON.parse(event.data);
        if (disposed || next.type === "pong") return;
        delay = 1000;
        setConnected(true);
        receive(next);
      };
      socket.onclose = (event) => {
        if (disposed) return;
        setConnected(false);
        if (event.code === 1008) {
          setError(
            "Access denied. Sign in again or ask your host for a valid link.",
          );
          return;
        }
        retry = setTimeout(connect, delay);
        delay = Math.min(delay * 2, 10000);
      };
    }
    connect();
    const heartbeat = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send("ping");
    }, 20000);
    return () => {
      disposed = true;
      clearTimeout(retry);
      clearInterval(heartbeat);
      socket?.close();
    };
  }, [room, mode, receive]);
  async function act(action: string, payload = {}) {
    if (busy || !connected) return;
    setBusy(true);
    setError("");
    try {
      const next = await api(`/rooms/${room}/commands`, {
        method: "POST",
        headers: token.current
          ? { Authorization: `Bearer ${token.current}` }
          : {},
        body: JSON.stringify({
          id: crypto.randomUUID(),
          revision: revision.current,
          action,
          payload,
        }),
      });
      receive(next);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return { state, connected, error, busy, act, offset };
}

function ShowPage({ mode }: { mode: "host" | "play" | "show" }) {
  const { room = "" } = useParams();
  const navigate = useNavigate();
  const { state: s, connected, error, busy, act, offset } = useShow(room, mode);
  const [answer, setAnswer] = useState("");
  const [now, setNow] = useState(Date.now());
  const [copied, setCopied] = useState("");
  const [adjustPlayer, setAdjustPlayer] = useState("0");
  const [adjustPoints, setAdjustPoints] = useState("100");
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    setAnswer("");
  }, [s?.index, s?.active]);
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
  const host = mode === "host" && s.you === "host";
  const player = s.players.find((p) => p.id === s.you);
  const activePlayer = s.players.find((p) => p.id === s.active);
  const seconds = s.paused
    ? Math.ceil(s.remaining ?? 0)
    : s.deadline
      ? Math.max(0, Math.ceil(s.deadline - (now + offset.current) / 1000))
      : null;
  const disabled = busy || !connected;
  const canBuzz = s.phase === "open" && !s.paused && !s.locked.includes(s.you);
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
  async function copyLink(label: string, path: string) {
    try {
      await navigator.clipboard.writeText(`${location.origin}${path}`);
      setCopied(label);
    } catch {
      setCopied("Copy the link from its text field.");
    }
  }
  return (
    <div className={`show-page ${mode}`}>
      <Header>
        <FullscreenButton />
        <span className={`connection ${connected ? "live" : ""}`}>
          {connected ? "Connected" : "Reconnecting…"}
        </span>
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
            <h1>
              Who Am I<span>?</span>
            </h1>
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
                {seconds !== null && (
                  <span className="timer" role="timer">
                    {seconds}s
                  </span>
                )}
              </div>
              {s.phase === "lobby" ? (
                <div className="intro">
                  <div className="mystery">?</div>
                  <h2>Know your champions?</h2>
                  <p>Three clues. Three contestants. One answer.</p>
                  <p className="muted">
                    Guess early for more points.
                    <br />A wrong answer costs {s.wrong_penalty} points.
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
              ) : (
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
              )}
              {s.phase === "revealed" && (
                <div className="answer-reveal">
                  <div className="eyebrow">THE CHAMPION IS</div>
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
              {mode === "play" && player && (
                <div className="player-actions">
                  {s.active === s.you &&
                  ["answering", "judging"].includes(s.phase) ? (
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
                          disabled ||
                          s.phase !== "answering" ||
                          s.paused ||
                          !answer.trim()
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
                          : canBuzz
                            ? "BUZZ IN"
                            : "Stand by"}
                      </button>
                      <p className="muted small">
                        {canBuzz ? "Click to claim your answer." : phaseLabel}
                      </p>
                    </>
                  )}
                </div>
              )}
            </section>
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
          </div>
          {host && (
            <aside className="host-controls">
              <section className="panel">
                <div className="panel-heading">
                  <h2>Round controls</h2>
                  <span className="tag">HOST ONLY</span>
                </div>
                <div className="host-answer">
                  <span className="eyebrow">ANSWER KEY</span>
                  <strong>
                    {s.answer || "Start to see the first champion"}
                  </strong>
                  {s.all_hints?.map((hint, i) => (
                    <p key={i} className={i < s.revealed ? "muted" : ""}>
                      {i + 1}. {hint}
                    </p>
                  ))}
                </div>
                {s.submission && (
                  <div className="submitted">
                    <span className="eyebrow">
                      {activePlayer?.name}'S ANSWER
                    </span>
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
                      {s.index + 1 === s.total
                        ? "Finish showdown"
                        : "Next champion →"}
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
                        disabled={
                          disabled || s.paused || s.revealed === s.hint_count
                        }
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
                  Keep contestant links private. Share the broadcast link with
                  OBS.
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
                        void copyLink(
                          s.players[i].name,
                          `/play/${room}#${token}`,
                        )
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
                    {copied.includes("Copy the")
                      ? copied
                      : `${copied} link copied`}
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
                  <button disabled={disabled || s.paused}>
                    Apply adjustment
                  </button>
                </form>
              </details>
            </aside>
          )}
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
              : "WHO AM I? · LEAGUE OF LEGENDS"}
          </span>
          <span>01 / 04 GAMES</span>
        </footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/host/:room" element={<ShowPage mode="host" />} />
        <Route path="/play/:room" element={<ShowPage mode="play" />} />
        <Route path="/show/:room" element={<ShowPage mode="show" />} />
        <Route
          path="*"
          element={
            <main className="empty">
              <h1>Page not found</h1>
              <Link to="/">Back to home</Link>
            </main>
          }
        />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);

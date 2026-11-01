import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Header } from "../components/layout/Header";
import type { Room, Show } from "../types/show";
export function LobbyPage() {
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

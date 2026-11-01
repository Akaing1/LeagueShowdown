import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Show } from "../types/show";
export function useShow(room: string, mode: string) {
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

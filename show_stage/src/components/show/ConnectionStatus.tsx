export function ConnectionStatus({ connected }: { connected: boolean }) {
  return (
    <span className={`connection ${connected ? "live" : ""}`}>
      {connected ? "Connected" : "Reconnecting…"}
    </span>
  );
}

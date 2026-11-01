import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { LobbyPage } from "../pages/LobbyPage";
import { HostPage } from "../pages/HostPage";
import { ContestantPage } from "../pages/ContestantPage";
import { BroadcastPage } from "../pages/BroadcastPage";
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/host/:room" element={<HostPage />} />
        <Route path="/play/:room" element={<ContestantPage />} />
        <Route path="/show/:room" element={<BroadcastPage />} />
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
  );
}

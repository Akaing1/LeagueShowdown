# Rats on the Rift

A League of Legends game show for **three contestants and one host**, built with Python/FastAPI and React/TypeScript. Version **0.1.1** implements the first playable game, **Who Am I?**

| Game | Status |
| --- | --- |
| Who Am I? | Playable |
| Splash Zone | Planned |
| EmoGG | Planned |
| ScribbLoL | Planned |

## Run locally

Requires Python 3.12+ and Node.js 22.12+ (Node 24 is used in CI).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
# Edit .env and choose a private SHOWDOWN_HOST_PASSWORD (at least 16 characters).
npm ci --prefix show_stage
npm run build --prefix show_stage
python -m uvicorn app.main:app --app-dir show_runner --env-file .env --host 127.0.0.1 --port 8008
```

Open **http://localhost:8008**. Sign in as host, enter three names, and create a showdown. Use **Contestant & broadcast links** to copy each contestant's link. Contestants need only a browser; voice/video can stay in Discord and OBS.

For frontend development, run the backend above and `npm run dev --prefix show_stage` in another terminal. Open **http://localhost:5173**; Vite proxies API and WebSocket traffic to port 8008. Keep all participants on the same origin.

For remote contestants, put the application behind HTTPS with WebSocket proxy support, set `SHOWDOWN_SECURE_COOKIE=1`, and use that public origin for all links. The local URL is only accessible on your own computer. Run **one backend worker/process** for this version; live rooms and connections are coordinated in that process. Back up the SQLite database in `data/`.

## Play Who Am I?

1. **Start Who Am I?** reveals the first clue and automatically opens the buzzers. The host can see the champion and all clues privately.
2. Every new champion round starts with buzzers open. Wrong answers and timeouts automatically promote the next queued contestant with a fresh 15-second timer; if nobody is queued, buzzers reopen for eligible contestants. Revealing a clue keeps buzzers open. The first eligible buzz starts an answer; later buzzes join a queue in server acceptance order, including while the host judges an answer. Internet latency can affect close races.
3. The contestant has **15 seconds** to submit a champion name or answer aloud. The host judges using **Correct** or **Incorrect**. A typed answer stops the timer while awaiting judgment; the host may also judge a spoken answer before the timer expires.
4. Correct answers earn **200** points on the first clue and **100** points on any of the remaining three clues. The default pack contains **eight rounds**. A wrong answer or expired answer timer costs **100 points**. Negative totals are allowed.
5. After a wrong answer or timeout, only that contestant is locked until the **next question**. Additional clues do not reset lockouts. A correct answer or the next question clears the queue. If all three contestants miss, reveal the answer and advance.
6. A correct answer reveals the champion to everyone. **Reveal answer / skip** ends an unanswered question without adding a penalty to contestants who did not answer. Advance with **Next champion**.
7. After the last champion, choose **Finish showdown**. The highest score wins; tied leaders are shown as a tie. A tiebreaker is not implemented yet.

The host can **pause/resume**, **adjust scores**, or **undo** up to 30 actions. Undo restores the previous state and pauses an active round so the host can review it before resuming. Restoring an answering turn gives that contestant a fresh 15 seconds. Undo cannot make contestants forget a champion that was already revealed.

## Screens and access

- `/` — password-protected host sign-in, show creation, and saved shows.
- `/host/{room}` — host console with answer key, judging, links, scores, and recovery controls.
- `/play/{room}#{private-key}` — a private seat for one contestant. The key is removed from the address bar and saved in that tab's session storage to survive refresh. Reopen the original link to restore a seat in a new tab/browser.
- `/show/{room}` — public broadcast view for an OBS browser source, typically at **1920 × 1080**. It explicitly requests public data even if the same browser is signed in as host.

Keep seat links private: anyone with a link can act as that contestant. The broadcast link is read-only and anyone with that link can view the show. Do not capture your host console on stream.

The server owns scores, timer deadlines, buzzer decisions, and round progression. It sends only revealed clues to contestants and the audience, and sends typed submissions only to the host and their author. Mutations require a current state revision and deduplicate accepted command IDs. Rooms, invites, scores, question packs, and undo history are saved transactionally in SQLite. Refresh/reconnect retrieves the current state. An unpaused answer timer continues across a server restart and expires when the server recovers; pause before planned downtime.

## Question packs

Eight sample League questions are included in `show_runner/app/content/who_am_i/default.json`. Before hosting a full episode, review the clues and prepare a fresh pack. Built-in questions are source-visible rehearsal content; private episode packs should be kept outside the repository.

Set `SHOWDOWN_QUESTIONS` in `.env` to an absolute path to a JSON file with 1–100 questions:

```json
[
  {
    "answer": "Ahri",
    "hints": ["A subtle clue", "A clearer clue", "Another clue", "An obvious clue"],
    "points": [200, 100, 100, 100]
  }
]
```

Each question supports 1–6 clues with one point value per clue. Packs are validated at startup and copied into each new show; changing the pack affects newly created shows after restarting the backend. There is no browser question editor yet.

## Checks

```bash
python -m pytest -q
python -m ruff check show_runner
python -m ruff format --check show_runner
npm run build --prefix show_stage
cd show_stage
npx playwright install chromium
npm run test:e2e
```

The browser test builds and starts its own test server when port 8008 is available, then exercises a host, three isolated contestant sessions, and a broadcast page sharing the host's cookies. It checks private answers, scoring, lockouts, undo, refresh recovery, and mobile overflow. Stop any regular server on port 8008 first; local tests may reuse an existing server and expect the test password. Screenshots are written into Playwright's ignored `test-results/` directory.

CI runs the backend tests and lint checks, the TypeScript/production build, and the browser test. Test credentials apply only to the isolated CI/test server.

## Project layout

- `show_runner/app/main.py` — application composition and startup/shutdown.
- `show_runner/app/api/` — HTTP routes, WebSocket connections, security middleware, and frontend serving.
- `show_runner/app/services/` — authentication, room commands, timers, and broadcasts.
- `show_runner/app/models/` — validated request and question schemas.
- `show_runner/app/games/who_am_i/` — game rules and role-specific projections.
- `show_runner/app/storage/` — SQLite persistence.
- `show_runner/app/content/who_am_i/` — bundled question packs.
- `show_runner/tests/` — API, game-rule, and storage tests with shared fixtures.
- `show_stage/src/app/` and `pages/` — routing and screen composition.
- `show_stage/src/components/` — shared layout, controls, and show components.
- `show_stage/src/games/who_am_i/` — clue cards and host/contestant controls.
- `show_stage/src/hooks/`, `api/`, and `types/` — live room state, HTTP client, and TypeScript contracts.
- `show_stage/src/styles/` — theme and show stylesheets.
- `show_stage/tests/e2e/` — browser integration tests.
- `docs/architecture.md` — ownership boundaries and extension guidance.

The original prototype has been removed; its source remains available in Git history.

Splash Zone and EmoGG will reuse the room, authentication, scores, and live-screen foundation. They do not have playable implementations in the new application yet.

This is an independent community project and is not endorsed by Riot Games.

Use **Fullscreen** in the game header on host, contestant, or broadcast screens. Use **Exit fullscreen** or Escape to leave. For OBS browser sources, use the broadcast link directly at your chosen resolution.

New rooms use the current question pack. Existing rooms retain the questions and scoring they were created with.

## ScribbLoL

Select **ScribbLoL** when creating a showdown. Six ability prompts rotate the artist through all three seats twice. Only the artist and host see the prompt; everyone sees completed strokes. Draw with mouse, touch, or pen using brush colors, an eraser, undo stroke, and clear canvas. The artist cannot buzz.

Each round has 90 seconds of drawing time. Drawing and its clock pause while contestants answer or the host judges; each active guesser gets the existing 15-second answer timer. Other eligible contestants can queue their buzz. A wrong answer or timeout uses that guesser's single attempt for the round, with no points deducted. The first correct guess awards **200 to the guesser and 200 to the artist**, ends the round, and clears the queue. If drawing time expires, both guessers miss, or the host ends an unsolved round, only the artist loses **100 points**. The host judges ability names manually, including acceptable alternate names.

The default pack is `show_runner/app/content/scribblol/default.json`. Prompts are source-visible rehearsal material. The canvas stores at most 200 strokes of 128 points each; use undo/clear if it fills. Saved drawings, timers, and scores survive reconnects/restarts. The host's undo restores the previous game action and pauses; artists undo individual strokes separately.

### Splash Zone

Choose **Splash Zone** when creating a showdown. Each room selects eight distinct
random champions from the bundled Data Dragon 16.22.1 roster, using their base
splash art. Each round starts at a random crop at 12× zoom and smoothly reveals
the full image over 30 seconds of active zoom time.

Buzzing freezes the shared zoom. Other contestants can queue while someone is
answering or being judged; an incorrect guess or answer timeout promotes the next
queued contestant. Once the queue is empty, zooming resumes from the saved point.
Wrong guessers are locked out until the next round. Correct guesses earn 200
points; wrong guesses and answer timeouts lose 100. After 30 seconds the full
image stays available to remaining guessers. The host reveals/skips if nobody
gets it. Host pause/resume, undo and reconnect preserve the shared clock and crop.

Images load directly from Riot's public Data Dragon CDN, so participant browsers
need internet access. Loading failures show a retry button; the host can pause or
skip if needed. This is a host-led party game: the image URL identifies the
champion to someone inspecting browser network traffic, so contestants should
play without developer tools.

Asset source and URL format: https://developer.riotgames.com/docs/lol#data-dragon
League of Legends splash art and champion data belong to Riot Games.

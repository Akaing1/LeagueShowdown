# Project architecture

## Show runner

`app/main.py` composes the application and owns startup/shutdown. `config.py` resolves environment settings, content paths, and validated question packs. The public ASGI entry point remains `app.main:app`.

`api/` adapts HTTP and WebSocket requests to authentication and room services. `models/` holds validation schemas. `services/` coordinates serialized commands, undo, persistence, timer expiry, and role-specific broadcasts. `games/who_am_i/rules.py` owns pure rules and public/private game projections; it does not depend on FastAPI or SQLite. `storage/sqlite.py` owns database access. JSON packs belong in `content/who_am_i/`, and setuptools includes them as package data.

Room state and database schema are unchanged. Existing room snapshots, command IDs, invite tokens, and host cookies retain their formats. The single-worker requirement still applies.

## Show stage

`main.tsx` only mounts React and global CSS. `app/App.tsx` declares routes. Host, contestant, and broadcast page entry points share `pages/ShowPage.tsx` for common screen composition.

Shared branding, fullscreen, connection state, and scores live under `components/`. Who Am I clue cards and gameplay controls live under `games/who_am_i/`. `hooks/useShow.ts` owns authenticated HTTP/WebSocket room state and commands; `hooks/useClock.ts` provides the display clock. `api/client.ts` handles HTTP requests and errors. `types/show.ts` defines transport types. CSS belongs in `styles/`; add an `assets/` directory when image or sound assets are introduced.

## Tests and future games

Backend tests are grouped under `tests/api`, `tests/games`, and `tests/storage`; shared fixtures and request helpers live at the test root. Playwright scenarios live under `show_stage/tests/e2e`.

New games should add their rules under `app/games/<game>/`, question data under `app/content/<game>/`, and React components under `src/games/<game>/`. Reuse shared authentication, room persistence, and presentation components. Introduce game dispatch when a second game is implemented rather than creating empty game packages now.

## Updating a checkout

After pulling this refactor, reinstall the editable Python package (`python -m pip install -e .`), rebuild with `npm run build --prefix show_stage`, and restart using the existing startup command. No database migration is needed. Ignored cache files may remain in old folders after Git moves the source; they are not active code. Avoid repository-wide cleanup commands.

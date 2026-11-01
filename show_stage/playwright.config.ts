import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

export default defineConfig({
  testDir: "./tests/e2e",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8008",
    viewport: { width: 1440, height: 1000 },
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE }
      : {},
  },
  webServer: {
    command:
      "npm run build && python -m uvicorn app.main:app --app-dir ../show_runner --port 8008",
    url: "http://127.0.0.1:8008/api/health",
    reuseExistingServer: !process.env.CI,
    env: {
      SHOWDOWN_HOST_PASSWORD: "local-browser-test-password",
      SHOWDOWN_DB: join(tmpdir(), `showdown-e2e-${process.pid}.sqlite3`),
    },
  },
});

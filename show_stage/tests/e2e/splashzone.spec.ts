import { test, expect } from "@playwright/test";

test("splash zoom pauses across queued guesses and resumes without jumping", async ({
  page,
  browser,
}) => {
  await page
    .context()
    .route("https://ddragon.leagueoflegends.com/**", (route) =>
      route.fulfill({
        contentType: "image/svg+xml",
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="1215" height="717"><rect width="1215" height="717" fill="#d7b46a"/></svg>',
      }),
    );
  await page.goto("/");
  await page.getByLabel("Host password").fill("local-browser-test-password");
  await page.getByRole("button", { name: "Enter host console" }).click();
  await page.getByLabel("Game", { exact: true }).selectOption("splash_zone");
  for (const [i, name] of ["One", "Two", "Three"].entries())
    await page.getByLabel(`Contestant ${i + 1}`).fill(name);
  await page.getByRole("button", { name: "Create showdown" }).click();
  await page.getByText("Contestant & broadcast links", { exact: true }).click();
  const links = await page
    .locator(".invite input")
    .evaluateAll((inputs) => inputs.map((i) => (i as HTMLInputElement).value));
  const context = await browser.newContext();
  await context.route("https://ddragon.leagueoflegends.com/**", (route) =>
    route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="1215" height="717"><rect width="1215" height="717" fill="#d7b46a"/></svg>',
    }),
  );
  const one = await context.newPage(),
    two = await context.newPage();
  await one.goto(links[0]);
  await two.goto(links[1]);
  await expect(one.locator(".connection")).toHaveText("Connected");
  await expect(two.locator(".connection")).toHaveText("Connected");
  await page.getByRole("button", { name: "Start Splash Zone" }).click();
  const art = page.locator(".splash-frame img");
  await expect(art).toBeVisible();
  const scale = () =>
    art.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a);
  const initial = await scale();
  await expect.poll(scale).toBeLessThan(initial - 0.1);
  await one.getByRole("button", { name: "BUZZ IN", exact: true }).click();
  await expect(page.locator(".answer-countdown")).toContainText("One");
  const frozen = await scale();
  await two.getByRole("button", { name: "BUZZ IN", exact: true }).click();
  await expect(
    two.getByRole("button", { name: "Queued · 1 in line" }),
  ).toBeDisabled();
  expect(await scale()).toBeCloseTo(frozen, 4);
  await page.getByRole("button", { name: "✕ Incorrect", exact: true }).click();
  await expect(page.locator(".answer-countdown")).toContainText("Two");
  expect(await scale()).toBeCloseTo(frozen, 4);
  await page.getByRole("button", { name: "✕ Incorrect", exact: true }).click();
  await expect.poll(scale).toBeLessThan(frozen - 0.1);
  await page.getByRole("button", { name: "Pause show", exact: true }).click();
  await expect(page.locator(".status")).toHaveText("Show paused");
  const paused = await scale();
  await one.reload();
  await expect(one.locator(".status")).toHaveText("Show paused");
  expect(
    await one
      .locator(".splash-frame img")
      .evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a),
  ).toBeCloseTo(paused, 4);
  await page.getByRole("button", { name: "Resume show", exact: true }).click();
  await page.getByRole("button", { name: "Reveal answer / skip" }).click();
  await expect(page.locator(".answer-reveal h2")).not.toBeEmpty();
  expect(await scale()).toBe(1);
  await page.getByRole("button", { name: "Next champion" }).click();
  await expect(page.locator(".round-label")).toContainText("QUESTION 2 / 8");
  expect(await scale()).toBeGreaterThan(10);
  await context.close();
});

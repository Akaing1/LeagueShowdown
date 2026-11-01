import { test, expect } from "@playwright/test";

test("host runs a round with three private contestants and a safe broadcast view", async ({
  page,
  browser,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByLabel("Host password").fill("local-browser-test-password");
  await page.getByRole("button", { name: "Enter host console" }).click();
  for (const [i, name] of ["Rat", "Meinya", "Minami"].entries()) {
    await page.getByLabel(`Contestant ${i + 1}`).fill(name);
  }
  await page.getByRole("button", { name: "Create showdown" }).click();
  await expect(page.getByText("HOST CONSOLE")).toBeVisible();
  await expect(
    page.getByText("Connected", { exact: true }).first(),
  ).toBeVisible();
  await page.getByText("Contestant & broadcast links", { exact: true }).click();
  const links = await page
    .locator(".invite input")
    .evaluateAll((inputs) =>
      inputs.map((input) => (input as HTMLInputElement).value),
    );
  expect(links).toHaveLength(3);
  const contexts = await Promise.all(links.map(() => browser.newContext()));
  const players = await Promise.all(
    contexts.map((context) => context.newPage()),
  );
  for (const [i, player] of players.entries()) {
    player.on("pageerror", (error) => errors.push(error.message));
    await player.goto(links[i]);
    await expect(player.locator(".connection")).toHaveText("Connected");
    expect(player.url()).not.toContain("#");
  }
  const broadcast = await page.context().newPage(); // Deliberately shares host auth.
  await broadcast.goto(page.url().replace("/host/", "/show/"));
  await expect(broadcast.locator(".connection")).toHaveText("Connected");
  await expect(broadcast.getByText("HOST ONLY")).toHaveCount(0);
  await broadcast
    .getByRole("button", { name: "Fullscreen", exact: true })
    .click();
  await expect
    .poll(() => broadcast.evaluate(() => Boolean(document.fullscreenElement)))
    .toBe(true);
  await broadcast
    .getByRole("button", { name: "Exit fullscreen", exact: true })
    .click();
  await expect
    .poll(() => broadcast.evaluate(() => Boolean(document.fullscreenElement)))
    .toBe(false);
  await page.getByRole("button", { name: "Start Who Am I?" }).click();
  await expect(page.locator(".host-answer strong")).toHaveText("Ezreal");
  for (const player of [...players, broadcast]) {
    await expect(player.locator(".clue").first()).toContainText("I never miss!");
    await expect(player.getByText("Ezreal", { exact: true })).toHaveCount(0);
    await expect(player.locator(".clue")).toHaveCount(4);
    for (const hint of [
      "I love double rainbows",
      "Your museum is not safe with me",
      "Twinkies",
    ]) {
      await expect(player.getByText(hint, { exact: true })).toHaveCount(0);
    }
  }
  await expect(
    players[0].getByRole("button", { name: "BUZZ IN", exact: true }),
  ).toBeEnabled();
  await players[0]
    .getByRole("button", { name: "BUZZ IN", exact: true })
    .click();
  await expect(players[0].getByLabel("Your answer")).toBeEnabled();
  await expect(
    players[1].getByRole("button", { name: "Stand by" }),
  ).toBeDisabled();
  await players[0].getByLabel("Your answer").fill("Garen");
  await players[0].getByRole("button", { name: "Lock in answer" }).click();
  await expect(page.locator(".submitted strong")).toHaveText("Garen");
  await expect(broadcast.getByText("Garen", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Incorrect", exact: false }).click();
  await expect(
    players[0].getByRole("button", { name: "Wait for the next clue" }),
  ).toBeDisabled();
  await expect(
    page.locator(".score-card").first().locator(".score"),
  ).toContainText("-100");
  await page.getByRole("button", { name: "Reveal next clue" }).click();
  await page.getByRole("button", { name: "Open buzzers", exact: true }).click();
  await players[1]
    .getByRole("button", { name: "BUZZ IN", exact: true })
    .click();
  await players[1].getByLabel("Your answer").fill("Ezreal");
  await players[1].getByRole("button", { name: "Lock in answer" }).click();
  await expect(page.locator(".submitted strong")).toHaveText("Ezreal");
  await page.getByRole("button", { name: "✓ Correct", exact: true }).click();
  await expect(broadcast.locator(".answer-reveal h2")).toHaveText("Ezreal");
  await expect(
    players[1].locator(".score-card").nth(1).locator(".score"),
  ).toContainText("100");
  await page.getByRole("button", { name: "Undo last action" }).click();
  await expect(page.locator(".status")).toHaveText("Show paused");
  await expect(
    page.locator(".score-card").nth(1).locator(".score"),
  ).toContainText("0");
  await expect(broadcast.locator(".answer-reveal")).toHaveCount(0);
  await page.getByRole("button", { name: "Resume show" }).click();
  await page.getByRole("button", { name: "✓ Correct", exact: true }).click();
  await players[1].reload();
  await expect(players[1].locator(".connection")).toHaveText("Connected");
  await expect(
    players[1].locator(".score-card").nth(1).locator(".score"),
  ).toContainText("100");
  await page.screenshot({
    path: testInfo.outputPath("host.png"),
    fullPage: true,
  });
  await broadcast.screenshot({
    path: testInfo.outputPath("broadcast.png"),
    fullPage: true,
  });
  await players[0].setViewportSize({ width: 390, height: 844 });
  await players[0].screenshot({
    path: testInfo.outputPath("contestant-mobile.png"),
    fullPage: true,
  });
  expect(
    await players[0].evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
  for (const context of contexts) await context.close();
});

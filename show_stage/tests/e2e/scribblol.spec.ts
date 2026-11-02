import { test, expect } from "@playwright/test";

test("drawing stays private, canvas syncs, rewards and artist rotation work", async ({
  page,
  browser,
}) => {
  await page.goto("/");
  await page.getByLabel("Host password").fill("local-browser-test-password");
  await page.getByRole("button", { name: "Enter host console" }).click();
  await page.getByLabel("Game", { exact: true }).selectOption("scribblol");
  for (const [i, name] of ["Artist", "Guesser", "Queue"].entries())
    await page.getByLabel(`Contestant ${i + 1}`).fill(name);
  await page.getByRole("button", { name: "Create showdown" }).click();
  await page.getByText("Contestant & broadcast links", { exact: true }).click();
  const links = await page
    .locator(".invite input")
    .evaluateAll((inputs) => inputs.map((i) => (i as HTMLInputElement).value));
  const contexts = await Promise.all(links.map(() => browser.newContext()));
  const players = await Promise.all(contexts.map((c) => c.newPage()));
  for (const [i, p] of players.entries()) {
    await p.goto(links[i]);
    await expect(p.locator(".connection")).toHaveText("Connected");
  }
  const broadcast = await page.context().newPage();
  await broadcast.goto(page.url().replace("/host/", "/show/"));
  await page.getByRole("button", { name: "Start ScribbLoL" }).click();
  await expect(players[0].locator(".artist-prompt")).toContainText(
    "Rocket Grab",
  );
  for (const p of [players[1], players[2], broadcast])
    await expect(p.getByText(/Rocket Grab/)).toHaveCount(0);
  await expect(
    players[0].getByRole("button", { name: "BUZZ IN", exact: true }),
  ).toHaveCount(0);
  const canvas = players[0].getByRole("img", { name: "Shared drawing canvas" });
  const box = (await canvas.boundingBox())!;
  await players[0].mouse.move(box.x + 20, box.y + 20);
  await players[0].mouse.down();
  await players[0].mouse.move(box.x + 100, box.y + 100, { steps: 5 });
  await players[0].mouse.up();
  await expect(broadcast.locator(".drawing-canvas path")).toHaveCount(1);
  await players[1].reload();
  await expect(players[1].locator(".drawing-canvas path")).toHaveCount(1);
  await players[1]
    .getByRole("button", { name: "BUZZ IN", exact: true })
    .click();
  await expect(page.locator(".score-card.active")).toContainText("Guesser");
  await players[2]
    .getByRole("button", { name: "BUZZ IN", exact: true })
    .click();
  await expect(
    players[2].getByRole("button", { name: "Queued · 1 in line" }),
  ).toBeDisabled();
  await players[1].getByLabel("Your answer").fill("Rocket Grab");
  await players[1].getByRole("button", { name: "Lock in answer" }).click();
  await expect(page.locator(".submitted strong")).toHaveText("Rocket Grab");
  await page.getByRole("button", { name: "✓ Correct", exact: true }).click();
  await expect(broadcast.locator(".score").nth(0)).toContainText("200");
  await expect(broadcast.locator(".score").nth(1)).toContainText("200");
  await expect(broadcast.locator(".score").nth(2)).toHaveText("0POINTS");
  await page.getByRole("button", { name: "Next artist" }).click();
  await expect(players[1].locator(".artist-prompt")).toContainText(
    "Final Spark",
  );
  await expect(broadcast.locator(".drawing-canvas path")).toHaveCount(0);
  await page.getByRole("button", { name: "End round · artist −100" }).click();
  await expect(broadcast.locator(".score").nth(1)).toContainText("100");
  await expect(broadcast.locator(".score").nth(0)).toContainText("200");
  for (const context of contexts) await context.close();
});

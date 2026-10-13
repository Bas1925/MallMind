// Record a real, isolated browser session against a running local stack.
// From frontend/: PW_CHANNEL=msedge node scripts/record-demo.mjs
// The output is deliberately ignored by Git; upload a reviewed copy separately.
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium, expect } from "@playwright/test";

const base = process.argv[2] ?? "http://localhost:3000";
const output = path.resolve(process.argv[3] ?? "../.validation/mallmind-demo.webm");
await mkdir(path.dirname(output), { recursive: true });
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL, slowMo: 160 });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: path.join(path.dirname(output), "raw-video"), size: { width: 1440, height: 900 } },
});
const page = await context.newPage();
const video = page.video();
// Deliberate reading pauses for the recording, not synchronization assertions.
const hold = (seconds) => page.waitForTimeout(seconds * 1000);
async function endpoint(id, name) {
  const input = page.getByTestId(id);
  await input.fill(name);
  await page.getByTestId(`${id}-results`).getByRole("option", { name: new RegExp(name) }).click();
}

try {
  await page.goto(base + "/#stores");
  await expect(page.getByTestId("store-card").first()).toBeVisible();
  await hold(5);
  await page.locator("#directory-list").scrollIntoViewIfNeeded();
  await page.getByRole("searchbox", { name: "Search stores" }).fill("Nike");
  await hold(5);
  await page.getByTestId("store-card").getByRole("button", { name: "Nike", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Nike" })).toBeVisible();
  await hold(5);
  await page.getByRole("button", { name: "Take me here" }).click();
  await expect(page.getByTestId("route-summary")).toContainText("Nike");
  await page.getByTestId("route-summary").scrollIntoViewIfNeeded();
  await hold(6);

  await endpoint("to-select", "Apple");
  await page.getByText("Wheelchair", { exact: true }).click();
  await expect(page.getByTestId("route-instructions")).toContainText(/elevator/i);
  await page.getByTestId("route-summary").scrollIntoViewIfNeeded();
  await hold(6);
  await page.getByRole("tab", { name: "Level 1", exact: true }).click();
  await page.getByTestId("mall-map").scrollIntoViewIfNeeded();
  await hold(6);

  await page.getByRole("tab", { name: "Plan", exact: true }).click();
  for (const stop of ["Nike", "Zara", "Apple", "ATM — Ground", "Super-Pharm"]) {
    await page.getByTestId("tour-search").fill(stop);
    await page.getByTestId("tour-search").press("Enter");
  }
  await page.getByTestId("tour-optimize").click();
  await expect(page.getByTestId("tour-result")).toBeVisible();
  await page.getByTestId("tour-savings").scrollIntoViewIfNeeded();
  await hold(8);

  await page.getByRole("tab", { name: "Ask", exact: true }).click();
  await page.getByTestId("assistant-input").fill("خذني إلى Nike");
  await page.getByTestId("assistant-submit").click();
  await expect(page.getByTestId("assistant-answer")).toBeVisible();
  await page.getByTestId("assistant-answer").scrollIntoViewIfNeeded();
  await hold(7);
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("button", { name: "Stores & dining" }).click();
  await page.getByRole("searchbox", { name: "Search stores" }).clear();
  await page.evaluate(() => window.scrollTo(0, 0));
  await hold(4);
  await context.close();
  await video.saveAs(output);
  console.log(`Recorded real demo: ${output}`);
} finally {
  await browser.close();
}

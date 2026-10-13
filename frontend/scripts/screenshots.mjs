// Capture README screenshots from a running dev stack.
// Usage: node scripts/screenshots.mjs [baseUrl] [outDir]
import { mkdir } from "node:fs/promises";
import { chromium } from "@playwright/test";

const base = process.argv[2] ?? "http://localhost:3000";
const out = process.argv[3] ?? "../docs/screenshots";
await mkdir(out, { recursive: true });

// PW_CHANNEL=msedge (or chrome) reuses an installed browser instead of downloading one.
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL });

async function shoot(name, viewport, steps, view = "map") {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 2 });
  await page.goto(base + (view === "stores" ? "#stores" : "#map"));
  await page.getByTestId(view === "stores" ? "store-card" : "mall-map").first().waitFor();
  await steps(page);
  // A full-page screenshot does not scroll lazy images into view. Load the
  // directory logos first so the saved preview represents the whole page.
  if (view === "stores") {
    for (const logo of await page.locator(".store-card img[data-brand-logo]").all()) {
      await logo.scrollIntoViewIfNeeded();
      await logo.evaluate((image) => image.decode());
    }
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  await page.close();
  console.log(`${out}/${name}.png`);
}

async function pickEndpoint(page, testId, label) {
  const name = label.split(" · ")[0];
  const field = page.getByTestId(testId);
  await field.click();
  await field.fill(name);
  await page.getByTestId(`${testId}-results`).getByRole("option", { name: new RegExp(name) }).click();
}

async function route(page, from, to, profile) {
  await pickEndpoint(page, "from-select", from);
  await pickEndpoint(page, "to-select", to);
  if (profile) await page.getByText(profile, { exact: true }).click();
  await page.getByTestId("route-submit").click();
  await page.getByTestId("route-summary").waitFor();
}

const desktop = { width: 1440, height: 900 };
await shoot("overview", desktop, async () => {}, "stores");
await shoot("directory-mobile", { width: 390, height: 844 }, async () => {}, "stores");
await shoot("map", desktop, async () => {});

await shoot("route", desktop, (page) =>
  route(page, "Main Entrance · Ground Floor", "MUJI · Level 2", "Wheelchair"),
);

await shoot("plan", desktop, async (page) => {
  await page.getByRole("tab", { name: "Plan" }).click();
  for (const stop of ["Nike", "Zara", "Apple", "ATM — Ground", "Super-Pharm"]) {
    await page.getByTestId("tour-search").fill(stop);
    await page.getByTestId("tour-search").press("Enter");
  }
  await page.getByTestId("tour-optimize").click();
  await page.getByTestId("tour-savings").waitFor();
});

await shoot("ask", desktop, async (page) => {
  await pickEndpoint(page, "from-select", "Main Entrance · Ground Floor");
  await page.getByRole("tab", { name: "Ask" }).click();
  await page.getByTestId("assistant-input").fill("خذني إلى Nike");
  await page.getByTestId("assistant-submit").click();
  await page.getByTestId("assistant-answer").waitFor();
  await page.getByTestId("route-summary").waitFor();
});

await shoot("mobile", { width: 390, height: 844 }, (page) =>
  route(page, "Main Entrance · Ground Floor", "Apple · Level 1"),
);

await browser.close();

import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /A good day/ })).toBeVisible();
  await expect(page.getByTestId("store-card").first()).toBeVisible();
});

test("all real store logos load locally and appear in details", async ({ page }) => {
  const logos = page.locator(".store-card img[data-brand-logo]");
  await expect(logos).toHaveCount(10);
  for (const logo of await logos.all()) {
    await logo.scrollIntoViewIfNeeded();
    await expect(logo).toBeVisible();
    await expect.poll(() => logo.evaluate((element) => {
      const image = element as HTMLImageElement;
      return image.complete && image.naturalWidth > 0 && new URL(image.currentSrc).origin === location.origin;
    })).toBe(true);
  }
  await page.getByRole("searchbox", { name: "Search stores" }).fill("Nike");
  await page.getByTestId("store-card").getByRole("button", { name: "Nike", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Nike" }).getByRole("img", { name: "Nike logo" })).toBeVisible();
  await page.getByRole("dialog", { name: "Nike" }).getByRole("button", { name: "View on map", exact: true }).click();
  // The floor directory is shown only when no individual place is selected.
  await page.reload();
  const sidebarLogo = page.locator('.directory-avatar img[data-brand-logo="nike"]');
  await expect(sidebarLogo).toBeVisible();
  await sidebarLogo.scrollIntoViewIfNeeded();
  await expect.poll(() => sidebarLogo.evaluate((image) => (image as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
});

test("directory filters combine, reset, and fit a small viewport", async ({ page }) => {
  const cards = page.getByTestId("store-card");
  await expect(cards).toHaveCount(15);
  await page.getByRole("group", { name: "Store categories" }).getByRole("button", { name: /Fashion/ }).click();
  await page.getByRole("combobox", { name: "Filter by floor" }).selectOption("1");
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText("Adidas");
  await page.getByRole("searchbox", { name: "Search stores" }).fill("unknown shop");
  await expect(page.getByRole("heading", { name: "No places found" })).toBeVisible();
  await page.getByRole("button", { name: "Reset filters" }).click();
  await page.getByRole("searchbox", { name: "Search stores" }).fill("Nike");
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText("Nike");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});

test("store details support Escape, focus restoration, and real directions", async ({ page }) => {
  await page.getByRole("searchbox", { name: "Search stores" }).fill("Nike");
  const card = page.getByTestId("store-card").first();
  const details = card.getByRole("button", { name: "Nike", exact: true });
  await details.click();
  const dialog = page.getByRole("dialog", { name: "Nike" });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("Opening hours are not published");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(details).toBeFocused();
  await details.click();
  await dialog.getByRole("button", { name: "Take me here" }).click();
  await expect(page).toHaveURL(/#map$/);
  await expect(page.getByTestId("route-summary")).toContainText("Nike");
  await expect(page.getByTestId("route-summary")).toContainText("Main Entrance");
  await expect(page.getByTestId("route-path")).toBeVisible();
});

test("directory and planner share stops and invalidate an outdated plan", async ({ page }) => {
  await page.getByRole("button", { name: "Add Nike to my visit", exact: true }).click();
  await page.getByRole("button", { name: "Add Zara to my visit", exact: true }).click();
  await page.getByRole("button", { name: "Plan my route", exact: true }).click();
  await expect(page.getByTestId("tour-stops")).toContainText("Nike");
  await expect(page.getByTestId("tour-stops")).toContainText("Zara");
  await page.getByTestId("tour-optimize").click();
  await expect(page.getByTestId("tour-result")).toBeVisible();
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("button", { name: "Stores & dining" }).click();
  await page.getByRole("button", { name: "Add Apple to my visit", exact: true }).click();
  await page.getByRole("button", { name: "Plan my route", exact: true }).click();
  await expect(page.getByTestId("tour-stops")).toContainText("Apple");
  await expect(page.getByTestId("tour-result")).toHaveCount(0);
  await expect(page.getByTestId("route-summary")).toHaveCount(0);
  await page.getByTestId("tour-optimize").click();
  await expect(page.getByTestId("tour-order")).toContainText("Apple");
  await page.getByRole("tab", { name: "Ask", exact: true }).click();
  await page.getByRole("tab", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("tour-stops")).toContainText("Apple");
});

test("map handoff selects the right floor and Back restores directory filters", async ({ page }) => {
  await page.getByRole("searchbox", { name: "Search stores" }).fill("Apple");
  await page.getByTestId("store-card").getByRole("button", { name: "On the map" }).click();
  await expect(page.getByRole("tab", { name: "Level 1", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("location-card")).toContainText("Apple");
  await page.goBack();
  await expect(page.getByRole("searchbox", { name: "Search stores" })).toHaveValue("Apple");
  await expect(page.getByTestId("store-card")).toHaveCount(1);
});

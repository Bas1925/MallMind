import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/#map");
  await expect(page.getByTestId("mall-map")).toBeVisible();
});

test("keyboard search selects a place and the page fits the viewport", async ({ page }) => {
  const search = page.getByRole("combobox", { name: "Search", exact: true });
  await search.fill("Nike");
  await expect(page.getByRole("listbox", { name: "Places" }).getByRole("option", { name: /Nike/ })).toBeVisible();
  await search.press("Enter");
  await expect(page.getByTestId("location-card")).toContainText("Nike");
  const overflow = await page.evaluate(() =>
    document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
});

test("trip optimization is invalidated when the stops change", async ({ page }) => {
  await page.getByRole("tab", { name: "Plan", exact: true }).click();
  for (const name of ["Nike", "Zara", "Apple"]) {
    await page.getByTestId("tour-search").fill(name);
    await page.getByTestId("tour-search").press("Enter");
  }
  await page.getByTestId("tour-optimize").click();
  await expect(page.getByTestId("tour-result")).toBeVisible();
  await expect(page.getByTestId("route-summary")).toBeVisible();
  await page.getByRole("button", { name: "Remove Zara" }).click();
  await expect(page.getByTestId("tour-result")).toHaveCount(0);
  await expect(page.getByTestId("route-summary")).toHaveCount(0);
  await page.getByTestId("tour-optimize").click();
  await expect(page.getByTestId("tour-order")).toContainText("Apple");
  await expect(page.getByTestId("tour-order")).not.toContainText("Zara");
});

test("parking survives a reload and can be cleared", async ({ page }) => {
  await page.getByRole("tab", { name: "Park", exact: true }).click();
  await page.getByLabel("Level *", { exact: true }).fill("P2");
  await page.getByLabel("Zone", { exact: true }).fill("Blue");
  await page.getByLabel("Spot number", { exact: true }).fill("218");
  await page.getByTestId("parking-save").click();
  await page.reload();
  await expect(page.getByTestId("mall-map")).toBeVisible();
  await page.getByRole("tab", { name: "Park", exact: true }).click();
  await expect(page.getByTestId("saved-parking")).toContainText("218");
  await page.getByRole("button", { name: /clear/i }).click();
  await expect(page.getByLabel("Spot number", { exact: true })).toHaveValue("");
});

test("the concierge answers in Arabic and refuses an unknown store", async ({ page }) => {
  await page.getByRole("tab", { name: "Ask", exact: true }).click();
  await page.getByTestId("assistant-input").fill("أين Nike");
  await page.getByTestId("assistant-submit").click();
  await expect(page.getByTestId("assistant-answer")).toHaveAttribute("lang", "ar");
  await expect(page.getByTestId("assistant-answer")).toContainText("Nike");
  await page.getByTestId("assistant-input").fill("Where is Gucci?");
  await page.getByTestId("assistant-submit").click();
  await expect(page.getByTestId("assistant-answer")).toHaveAttribute("lang", "en");
  await expect(page.getByTestId("assistant-answer")).toContainText(/could not|couldn't|not find|no matching/i);
});

import { expect, test, type Page } from "@playwright/test";

async function pickEndpoint(page: Page, testId: string, name: string): Promise<void> {
  const field = page.getByTestId(testId);
  await field.click();
  await field.fill(name);
  await page.getByTestId(`${testId}-results`).getByRole("option", { name: new RegExp(name) }).click();
}

test("recruiter can request a real A* route on the NOVA map", async ({ page, request }) => {
  const health = await request.get("http://localhost:8000/api/v1/health");
  expect(health.ok(), "Backend must be running on :8000 for this E2E. Do not skip.").toBeTruthy();

  await page.goto("/#map");
  await expect(page.getByTestId("mall-map")).toBeVisible();

  await page.getByTestId("location-search").fill("Nike");
  await page.getByTestId("search-results").getByRole("option", { name: /Nike/ }).click();
  await expect(page.getByTestId("location-card")).toContainText("Nike");

  await pickEndpoint(page, "from-select", "Main Entrance");
  await pickEndpoint(page, "to-select", "Nike");
  await page.getByTestId("route-submit").click();

  await expect(page.getByTestId("route-path")).toBeVisible();
  await expect(page.getByTestId("route-summary")).toContainText("Main Entrance");
  await expect(page.getByTestId("route-summary")).toContainText("Nike");
  await expect(page.getByTestId("route-summary")).toContainText("m");
  await expect(page.getByTestId("route-summary")).toContainText("min");
  await expect(page.getByTestId("route-instructions")).toBeVisible();

  await pickEndpoint(page, "to-select", "Apple");
  await page.getByText("Wheelchair", { exact: true }).click();
  await expect(page.getByTestId("route-summary")).toContainText("Apple");
  await expect(page.getByTestId("route-instructions")).toContainText(/elevator/i);
  await page.getByTestId("route-submit").click();
  await expect(page.getByTestId("route-summary")).toContainText("Apple");
  await expect(page.getByTestId("continue-via")).toBeVisible();

  const groundPath = await page.getByTestId("route-path").first().getAttribute("d");
  await page.getByRole("tab", { name: "Level 1" }).click();
  await expect(page.getByRole("tab", { name: "Level 1" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("route-path")).toBeVisible();
  const levelPath = await page.getByTestId("route-path").first().getAttribute("d");
  expect(levelPath).not.toEqual(groundPath);
});

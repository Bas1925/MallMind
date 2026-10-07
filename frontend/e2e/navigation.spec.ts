import { expect, test } from "@playwright/test";

test("recruiter can request a real A* route on the NOVA map", async ({ page, request }) => {
  const health = await request.get("http://localhost:8000/api/v1/health");
  expect(health.ok(), "Backend must be running on :8000 for this E2E. Do not skip.").toBeTruthy();

  await page.goto("/");
  await expect(page.getByTestId("mall-map")).toBeVisible();

  await page.getByTestId("location-search").fill("Nike");
  await page.getByTestId("search-results").getByRole("button", { name: /Nike/ }).click();
  await expect(page.getByTestId("location-card")).toContainText("Nike");

  await page.getByTestId("from-select").selectOption({ label: "Main Entrance · Ground Floor" });
  await page.getByTestId("to-select").selectOption({ label: "Nike · Ground Floor" });
  await page.getByTestId("route-submit").click();

  await expect(page.getByTestId("route-path")).toBeVisible();
  await expect(page.getByTestId("route-summary")).toContainText("Main Entrance");
  await expect(page.getByTestId("route-summary")).toContainText("Nike");
  await expect(page.getByTestId("route-summary")).toContainText("m");
  await expect(page.getByTestId("route-summary")).toContainText("min");
  await expect(page.getByTestId("route-instructions")).toBeVisible();

  await page.getByTestId("to-select").selectOption({ label: "Apple · Level 1" });
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

import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

test.describe("Student recommendations journey", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.studentEmail);
  });

  test("recommendations page loads from nav", async ({ page }) => {
    await page.getByRole("link", { name: "Recommendations" }).click();
    await expect(page).toHaveURL(/\/student\/recommendations/);
    await expect(page.getByRole("heading", { name: "Recommendations" })).toBeVisible();
  });

  test("timeline page has no duplicate sidebar", async ({ page }) => {
    await page.goto("/student/timeline");
    await expect(page.getByRole("heading", { name: "Learning timeline" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Main navigation" })).toHaveCount(1);
  });
});

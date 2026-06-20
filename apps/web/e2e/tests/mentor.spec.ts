import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

test.describe("Mentor journeys", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.facultyEmail);
  });

  test("mentor queue page loads", async ({ page }) => {
    await page.goto("/mentor/queue");
    await expect(page.getByRole("heading", { name: "Mentor Queue" })).toBeVisible();
  });

  test("mentor queue lists cases or empty state", async ({ page }) => {
    await page.goto("/mentor/queue");
    const table = page.locator("table");
    const empty = page.getByText("Queue is empty");
    await expect(table.or(empty)).toBeVisible();
  });

  test("mentor can resolve a case when queue has items", async ({ page }) => {
    await page.goto("/mentor/queue");
    const caseLink = page.locator('a[href*="/mentor/cases/"]').first();
    const linkCount = await caseLink.count();
    test.skip(linkCount === 0, "No mentor cases in demo queue");

    await caseLink.click();
    await expect(page.getByRole("heading", { name: /Case ·/ })).toBeVisible();
    await page.locator("#resolution_reason").selectOption("STUDENT_CONTACTED");
    await page.getByRole("button", { name: "Resolve case" }).click();
    await expect(page.getByText("Case resolved")).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/mentor\/queue/);
  });

  test("admin health page loads for institute admin", async ({ page }) => {
    await loginAs(page, e2eConfig.adminEmail);
    await page.goto("/admin/health");
    await expect(page.getByRole("heading", { name: "Platform health" })).toBeVisible();
    await expect(page.getByText("Overall status")).toBeVisible({ timeout: 15_000 });
  });
});

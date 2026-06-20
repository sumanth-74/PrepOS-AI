import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

test.describe("Student journeys", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.studentEmail);
  });

  test("dashboard shows readiness KPIs", async ({ page }) => {
    await expect(page.getByText("Readiness score")).toBeVisible();
    await expect(page.getByText("Expected score")).toBeVisible();
  });

  test("onboarded student is not redirected to onboarding wizard", async ({ page }) => {
    await page.goto("/student/onboarding");
    await expect(page).toHaveURL(/\/student\/dashboard/);
  });

  test("activities page loads four forms", async ({ page }) => {
    await page.goto("/student/activities");
    await expect(page.getByRole("heading", { name: "Log activity" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Study session" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Revision" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Assessment" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "PYQ update" })).toBeVisible();
  });

  test("activity submission shows success toast", async ({ page }) => {
    await page.goto("/student/activities");
    const conceptSelect = page.locator("#concept_id").first();
    await conceptSelect.waitFor({ state: "visible" });
    const options = conceptSelect.locator("option");
    const optionCount = await options.count();
    test.skip(optionCount < 2, "Demo learning graph has no concepts to log activity against");
    await conceptSelect.selectOption({ index: 1 });
    await page.getByRole("button", { name: "Log study session" }).click();
    await expect(page.getByText("Study session logged")).toBeVisible({ timeout: 15_000 });
  });

  test("revision queue page loads", async ({ page }) => {
    await page.goto("/student/revision-queue");
    await expect(page.getByRole("heading", { name: "Revision Queue" })).toBeVisible();
  });

  test("learning graph page loads", async ({ page }) => {
    await page.goto("/student/learning-graph");
    await expect(page.getByRole("heading", { name: "Learning Graph" })).toBeVisible();
  });
});

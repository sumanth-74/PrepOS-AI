import { test, expect } from "@playwright/test";
import { e2eConfig, loginAs } from "../helpers/auth";

test.describe("Authentication", () => {
  test("student login reaches dashboard", async ({ page }) => {
    await loginAs(page, e2eConfig.studentEmail);
    await expect(page).toHaveURL(/\/student\/dashboard/);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("mentor login reaches mentor dashboard", async ({ page }) => {
    await loginAs(page, e2eConfig.facultyEmail);
    await expect(page).toHaveURL(/\/mentor\/dashboard/);
    await expect(page.getByRole("heading", { name: "Mentor Dashboard" })).toBeVisible();
  });

  test("admin login reaches admin dashboard", async ({ page }) => {
    await loginAs(page, e2eConfig.adminEmail);
    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole("heading", { name: "Admin dashboard" })).toBeVisible();
  });

  test("invalid credentials show error", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#tenant_slug").fill(e2eConfig.tenant);
    await page.locator("#email").fill("invalid@example.com");
    await page.locator("#password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText(/login failed|invalid|incorrect|unauthorized/i)).toBeVisible();
  });
});

import { test, expect } from "@playwright/test";

test.describe("Public smoke", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in to PrepOS" })).toBeVisible();
    await expect(page.locator("#tenant_slug")).toBeVisible();
  });

  test("register page renders", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: "Create your institute" })).toBeVisible();
  });
});

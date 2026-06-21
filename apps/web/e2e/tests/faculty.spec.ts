import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

test.describe("Faculty journeys", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.facultyEmail);
  });

  test("faculty workspace is reachable from mentor nav", async ({ page }) => {
    await page.getByRole("link", { name: "Faculty workspace" }).click();
    await expect(page).toHaveURL(/\/faculty$/);
    await expect(page.getByRole("heading", { name: "Faculty workspace" })).toBeVisible();
  });
});

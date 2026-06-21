import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

test.describe("Admin journeys", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.adminEmail);
  });

  test("admin lands on dashboard with sidebar sections", async ({ page }) => {
    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole("heading", { name: "Admin dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Copilot analytics" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Platform health" })).toBeVisible();
  });

  test("security sub-pages are reachable", async ({ page }) => {
    await page.goto("/admin/security/tenant-audit");
    await expect(page.getByRole("heading", { name: "Tenant audit" })).toBeVisible();

    await page.goto("/admin/security/knowledge");
    await expect(page.getByRole("heading", { name: "Knowledge security" })).toBeVisible();

    await page.goto("/admin/security/rate-limits");
    await expect(page.getByRole("heading", { name: "Rate limits" })).toBeVisible();
  });

  test("P11 platform pages load", async ({ page }) => {
    await page.goto("/admin/jobs");
    await expect(page.getByRole("heading", { name: "Background jobs" })).toBeVisible();

    await page.goto("/admin/platform-readiness");
    await expect(page.getByRole("heading", { name: "Platform readiness" })).toBeVisible();
  });

  test("agent ops pages load", async ({ page }) => {
    await page.goto("/admin/agent-evaluation");
    await expect(page.getByRole("heading", { name: "Agent evaluation" })).toBeVisible();

    await page.goto("/admin/approvals");
    await expect(page.getByRole("heading", { name: "Agent approval workflows" })).toBeVisible();
  });
});

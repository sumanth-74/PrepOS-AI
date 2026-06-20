import path from "node:path";

import { test, expect } from "@playwright/test";
import { loginAs, e2eConfig } from "../helpers/auth";

const fixturePath = path.join(__dirname, "../fixtures/sample-knowledge.txt");

test.describe("Admin knowledge operations", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, e2eConfig.adminEmail);
  });

  test("knowledge operations page shows metrics and source table", async ({ page }) => {
    await page.goto("/admin/knowledge");
    await expect(page.getByRole("heading", { name: "Knowledge operations" })).toBeVisible();
    await expect(page.getByText("Total sources")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Indexed chunks")).toBeVisible();
    await expect(page.getByText("Failed chunks")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Knowledge sources" })).toBeVisible();
  });

  test("admin can upload a knowledge source and view its status", async ({ page }) => {
    await page.goto("/admin/knowledge");
    await expect(page.getByRole("button", { name: "Upload source" })).toBeVisible();

    await page.getByRole("button", { name: "Upload source" }).click();
    await expect(page.getByRole("heading", { name: "Upload knowledge source" })).toBeVisible();

    const uniqueTitle = `E2E Polity Notes ${Date.now()}`;
    await page.locator("#knowledge-title").fill(uniqueTitle);

    const examSelect = page.locator("#knowledge-exam");
    await expect(examSelect.locator("option")).not.toHaveCount(1, { timeout: 15_000 });
    const firstExamValue = await examSelect.locator("option").nth(1).getAttribute("value");
    test.skip(!firstExamValue, "No active exams available for upload");
    await examSelect.selectOption(firstExamValue!);

    await page.locator("#knowledge-file").setInputFiles(fixturePath);
    await page.getByRole("button", { name: "Upload and index" }).click();

    await expect(page.getByText("Knowledge source uploaded")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("cell", { name: uniqueTitle })).toBeVisible({ timeout: 15_000 });

    const viewLink = page.getByRole("row", { name: new RegExp(uniqueTitle) }).getByRole("link", { name: "View" });
    await viewLink.click();

    await expect(page.getByRole("heading", { name: uniqueTitle })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Indexing progress")).toBeVisible();
    await expect(page.getByText("Chunk & failure metrics")).toBeVisible();
  });

  test("knowledge source detail page loads from list link", async ({ page }) => {
    await page.goto("/admin/knowledge");
    await expect(page.getByRole("heading", { name: "Knowledge sources" })).toBeVisible({ timeout: 15_000 });

    const viewLink = page.getByRole("link", { name: "View" }).first();
    const linkCount = await viewLink.count();
    test.skip(linkCount === 0, "No knowledge sources in demo tenant");

    await viewLink.click();
    await expect(page.getByText("Indexing progress")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Ingestion timestamps")).toBeVisible();
  });
});

export const e2eConfig = {
  tenant: process.env.E2E_TENANT ?? "prepos-demo",
  studentEmail: process.env.E2E_STUDENT_EMAIL ?? "student@prepos-demo.example.com",
  facultyEmail: process.env.E2E_FACULTY_EMAIL ?? "faculty@prepos-demo.example.com",
  adminEmail: process.env.E2E_ADMIN_EMAIL ?? "admin@prepos-demo.example.com",
  password: process.env.E2E_PASSWORD ?? "SecurePass123!",
};

export async function loginAs(
  page: import("@playwright/test").Page,
  email: string,
): Promise<void> {
  await page.goto("/login");
  await page.locator("#tenant_slug").fill(e2eConfig.tenant);
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(e2eConfig.password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

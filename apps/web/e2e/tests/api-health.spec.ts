import { test, expect } from "@playwright/test";

function apiOrigin(): string {
  const fromEnv = process.env.PLAYWRIGHT_API_ORIGIN;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
  return base.replace(/\/api\/v1\/?$/, "");
}

test.describe("API health smoke", () => {
  test("backend health endpoints respond", async ({ request }) => {
    const origin = apiOrigin();

    const health = await request.get(`${origin}/health`);
    expect(health.ok()).toBeTruthy();
    expect((await health.json()).status).toBe("ok");

    const ready = await request.get(`${origin}/health/ready`);
    expect(ready.ok()).toBeTruthy();

    const worker = await request.get(`${origin}/health/worker`);
    expect(worker.ok()).toBeTruthy();

    const outbox = await request.get(`${origin}/health/outbox`);
    expect(outbox.ok()).toBeTruthy();

    const ops = await request.get(`${origin}/health/ops`);
    expect(ops.ok()).toBeTruthy();
  });
});

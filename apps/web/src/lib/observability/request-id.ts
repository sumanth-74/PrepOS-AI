let counter = 0;

export function createRequestId(): string {
  counter += 1;
  const time = Date.now().toString(36);
  return `prepos-${time}-${counter}`;
}

export function logApiRequest(
  requestId: string,
  method: string,
  path: string,
  status: number,
  durationMs: number,
): void {
  if (process.env.NODE_ENV === "production") {
    console.info(
      JSON.stringify({
        type: "api_request",
        request_id: requestId,
        method,
        path,
        status,
        duration_ms: durationMs,
      }),
    );
    return;
  }

  console.debug(`[${requestId}] ${method} ${path} → ${status} (${durationMs}ms)`);
}

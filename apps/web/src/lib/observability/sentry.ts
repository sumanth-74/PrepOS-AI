type SentryLevel = "error" | "warning" | "info";

function isSentryEnabled(): boolean {
  return process.env.NEXT_PUBLIC_SENTRY_DSN !== undefined &&
    process.env.NEXT_PUBLIC_SENTRY_ENABLED === "true";
}

export function captureException(error: unknown, context?: Record<string, unknown>): void {
  if (!isSentryEnabled()) {
    if (process.env.NODE_ENV !== "production") {
      console.error("[observability] captureException", error, context);
    }
    return;
  }

  // Hook point for @sentry/nextjs when enabled in deployment.
  console.error("[sentry-disabled] captureException", error, context);
}

export function captureMessage(message: string, level: SentryLevel = "info"): void {
  if (!isSentryEnabled()) {
    if (process.env.NODE_ENV !== "production") {
      console.debug(`[observability] ${level}: ${message}`);
    }
    return;
  }

  console.info(`[sentry-disabled] ${level}: ${message}`);
}

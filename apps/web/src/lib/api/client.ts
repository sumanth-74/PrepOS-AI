import {
  ApiError,
  formatApiError,
  getApiBaseUrl,
} from "@/lib/api/errors";
import {
  isAuthPath,
  refreshAccessToken,
} from "@/lib/api/token-refresh";
import { createRequestId, logApiRequest } from "@/lib/observability/request-id";
import type { ApiErrorBody } from "@/lib/types/api";

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface RequestOptions {
  method?: HttpMethod;
  /** When true, skip automatic 401 refresh retry (used by refresh endpoint). */
  skipAuthRetry?: boolean;
  body?: unknown;
  token?: string | null;
  query?: Record<string, string | number | boolean | undefined | null>;
}

export interface FormRequestOptions {
  method?: "POST" | "PUT" | "PATCH";
  formData: FormData;
  token?: string | null;
  query?: Record<string, string | number | boolean | undefined | null>;
  skipAuthRetry?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${base}${normalized}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function executeFetch<T>(
  path: string,
  options: RequestOptions,
  token: string | null | undefined,
): Promise<T> {
  const { method = "GET", body, query } = options;
  const requestId = createRequestId();
  const started = performance.now();
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Request-ID": requestId,
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: "include",
    cache: "no-store",
  });

  logApiRequest(requestId, method, path, response.status, Math.round(performance.now() - started));

  if (response.status === 204) {
    return undefined as T;
  }

  let payload: ApiErrorBody | T | null = null;
  const text = await response.text();
  if (text) {
    payload = JSON.parse(text) as ApiErrorBody | T;
  }

  if (!response.ok) {
    throw new ApiError(
      formatApiError(payload as ApiErrorBody | null, response.statusText),
      response.status,
      payload as ApiErrorBody | null,
    );
  }

  return payload as T;
}

async function executeFetchForm<T>(
  path: string,
  options: FormRequestOptions,
  token: string | null | undefined,
): Promise<T> {
  const { method = "POST", formData, query } = options;
  const requestId = createRequestId();
  const started = performance.now();
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Request-ID": requestId,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: formData,
    credentials: "include",
    cache: "no-store",
  });

  logApiRequest(requestId, method, path, response.status, Math.round(performance.now() - started));

  let payload: ApiErrorBody | T | null = null;
  const text = await response.text();
  if (text) {
    payload = JSON.parse(text) as ApiErrorBody | T;
  }

  if (!response.ok) {
    throw new ApiError(
      formatApiError(payload as ApiErrorBody | null, response.statusText),
      response.status,
      payload as ApiErrorBody | null,
    );
  }

  return payload as T;
}

async function executeFetchText(
  path: string,
  options: RequestOptions,
  token: string | null | undefined,
): Promise<string> {
  const { method = "GET", body, query } = options;
  const requestId = createRequestId();
  const started = performance.now();
  const headers: Record<string, string> = {
    Accept: "text/csv,text/plain,*/*",
    "X-Request-ID": requestId,
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: "include",
    cache: "no-store",
  });

  logApiRequest(requestId, method, path, response.status, Math.round(performance.now() - started));

  const text = await response.text();
  if (!response.ok) {
    let payload: ApiErrorBody | null = null;
    try {
      payload = text ? (JSON.parse(text) as ApiErrorBody) : null;
    } catch {
      payload = null;
    }
    throw new ApiError(
      formatApiError(payload, response.statusText),
      response.status,
      payload,
    );
  }

  return text;
}

export async function apiRequestText(
  path: string,
  options: RequestOptions = {},
): Promise<string> {
  const { token, skipAuthRetry } = options;

  try {
    return await executeFetchText(path, options, token);
  } catch (error) {
    const shouldRetry =
      !skipAuthRetry &&
      !isAuthPath(path) &&
      token &&
      error instanceof ApiError &&
      error.status === 401;

    if (!shouldRetry) {
      throw error;
    }

    const newToken = await refreshAccessToken();
    if (!newToken) {
      throw error;
    }

    return executeFetchText(path, options, newToken);
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { token, skipAuthRetry } = options;

  try {
    return await executeFetch<T>(path, options, token);
  } catch (error) {
    const shouldRetry =
      !skipAuthRetry &&
      !isAuthPath(path) &&
      token &&
      error instanceof ApiError &&
      error.status === 401;

    if (!shouldRetry) {
      throw error;
    }

    const newToken = await refreshAccessToken();
    if (!newToken) {
      throw error;
    }

    return executeFetch<T>(path, options, newToken);
  }
}

export async function apiRequestForm<T>(
  path: string,
  options: FormRequestOptions,
): Promise<T> {
  const { token, skipAuthRetry } = options;

  try {
    return await executeFetchForm<T>(path, options, token);
  } catch (error) {
    const shouldRetry =
      !skipAuthRetry &&
      !isAuthPath(path) &&
      token &&
      error instanceof ApiError &&
      error.status === 401;

    if (!shouldRetry) {
      throw error;
    }

    const newToken = await refreshAccessToken();
    if (!newToken) {
      throw error;
    }

    return executeFetchForm<T>(path, options, newToken);
  }
}

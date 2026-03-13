export type ApiSuccess<T> = { success: true; data: T; meta: { timestamp: string; request_id: string } };
export type ApiError = { success: false; error: { code: string; message: string; details: Record<string, unknown> } };
export type ApiEnvelope<T> = ApiSuccess<T> | ApiError;

export class ApiRequestError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(message: string, code = "UNKNOWN", details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.details = details;
  }
}

const DEFAULT_BASE_URL = "http://127.0.0.1:8001";

export function apiBaseUrl(): string {
  const env = (import.meta.env ?? {}) as unknown as { VITE_API_BASE_URL?: string };
  return env.VITE_API_BASE_URL || DEFAULT_BASE_URL;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
  });

  const text = await res.text();
  let json: ApiEnvelope<T> | null = null;
  try {
    json = text ? (JSON.parse(text) as ApiEnvelope<T>) : null;
  } catch {
    // ignore; handle below
  }

  if (!res.ok) {
    throw new ApiRequestError(`HTTP ${res.status} calling ${path}`, "HTTP_ERROR", { status: res.status, body: text });
  }
  if (!json) throw new ApiRequestError(`Empty response calling ${path}`, "EMPTY_RESPONSE");
  if (!("success" in json)) throw new ApiRequestError(`Invalid response calling ${path}`, "INVALID_RESPONSE", { body: json as unknown });
  if (!json.success) throw new ApiRequestError(json.error.message, json.error.code, json.error.details);
  return json.data;
}

export async function apiPostForm<T>(path: string, formData: FormData, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    method: "POST",
    body: formData,
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
  });

  const text = await res.text();
  let json: ApiEnvelope<T> | null = null;
  try {
    json = text ? (JSON.parse(text) as ApiEnvelope<T>) : null;
  } catch {
    // ignore; handle below
  }

  if (!res.ok) {
    throw new ApiRequestError(`HTTP ${res.status} calling ${path}`, "HTTP_ERROR", { status: res.status, body: text });
  }
  if (!json) throw new ApiRequestError(`Empty response calling ${path}`, "EMPTY_RESPONSE");
  if (!("success" in json)) throw new ApiRequestError(`Invalid response calling ${path}`, "INVALID_RESPONSE", { body: json as unknown });
  if (!json.success) throw new ApiRequestError(json.error.message, json.error.code, json.error.details);
  return json.data;
}


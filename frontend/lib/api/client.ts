/**
 * API client for backend communication.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public errorCode: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends RequestInit {
  token?: string | null;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorCode = "UNKNOWN_ERROR";
    let message = "An error occurred";
    let details: Record<string, unknown> | undefined;

    try {
      const errorData = await response.json();
      errorCode = errorData.error_code || errorCode;
      message = errorData.message || message;
      details = errorData.details;
    } catch {
      message = response.statusText;
    }

    throw new ApiError(response.status, errorCode, message, details);
  }

  return response.json();
}

export async function apiGet<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    method: "GET",
    headers,
  });

  return handleResponse<T>(response);
}

export async function apiPost<T>(
  endpoint: string,
  data?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    method: "POST",
    headers,
    body: data ? JSON.stringify(data) : undefined,
  });

  return handleResponse<T>(response);
}

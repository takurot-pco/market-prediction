/**
 * Auth API client - SPEC Section 5 compliant.
 */

import type { TokenResponse, User } from "@/types/auth";
import { apiGet, apiPost } from "./client";

const AUTH_PREFIX = "/api/v1/auth";

/**
 * Get the login URL for SSO authentication.
 * In mock mode, this redirects directly to callback.
 */
export function getLoginUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${apiUrl}${AUTH_PREFIX}/login`;
}

/**
 * Exchange authorization code for access token.
 */
export async function authCallback(code: string): Promise<TokenResponse> {
  return apiGet<TokenResponse>(`${AUTH_PREFIX}/callback?code=${encodeURIComponent(code)}`);
}

/**
 * Logout the current user.
 */
export async function logout(token: string): Promise<void> {
  await apiPost<{ message: string }>(`${AUTH_PREFIX}/logout`, undefined, { token });
}

/**
 * Get current user information.
 */
export async function getCurrentUser(token: string): Promise<User> {
  return apiGet<User>(`${AUTH_PREFIX}/me`, { token });
}

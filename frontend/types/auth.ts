/**
 * Authentication type definitions - SPEC Section 5 compliant.
 */

export type UserRole = "user" | "moderator" | "admin";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  department: string | null;
  balance: number;
}

/**
 * Role hierarchy levels for permission checking.
 * Higher number = higher privilege.
 */
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 1,
  moderator: 2,
  admin: 3,
};

/**
 * Check if a user role has the required permission level.
 * Uses role hierarchy: admin > moderator > user.
 */
export function hasRequiredRole(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthActions {
  login: () => Promise<void>;
  loginWithCallback: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  setToken: (token: string) => void;
}

export type AuthStore = AuthState & AuthActions;

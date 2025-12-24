/**
 * Authentication type definitions - SPEC Section 5 compliant.
 */

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: "user" | "moderator" | "admin";
  department: string | null;
  balance: number;
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

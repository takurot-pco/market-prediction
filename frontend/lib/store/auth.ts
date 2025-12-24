/**
 * Auth store using Zustand - manages authentication state.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthStore, User } from "@/types/auth";
import { authCallback, getCurrentUser, logout as logoutApi, getLoginUrl } from "@/lib/api/auth";

const TOKEN_KEY = "auth_token";

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async () => {
        // Redirect to backend login endpoint
        window.location.href = getLoginUrl();
      },

      loginWithCallback: async (code: string) => {
        set({ isLoading: true, error: null });
        try {
          const tokenResponse = await authCallback(code);
          const token = tokenResponse.access_token;
          set({ token });

          // Fetch user info
          const user = await getCurrentUser(token);
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : "Login failed",
            isLoading: false,
            token: null,
            user: null,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: async () => {
        const { token } = get();
        set({ isLoading: true, error: null });
        try {
          if (token) {
            await logoutApi(token);
          }
        } catch {
          // Ignore logout API errors
        } finally {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      fetchUser: async () => {
        const { token } = get();
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true, error: null });
        try {
          const user = await getCurrentUser(token);
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch {
          // Token is invalid or expired
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      clearError: () => set({ error: null }),

      setToken: (token: string) => set({ token }),
    }),
    {
      name: TOKEN_KEY,
      partialize: (state) => ({ token: state.token }),
    }
  )
);

// Selector hooks for convenience
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);

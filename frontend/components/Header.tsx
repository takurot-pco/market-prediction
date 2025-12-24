"use client";

import Link from "next/link";
import { useAuthStore } from "@/lib/store/auth";

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo / Title */}
          <Link href="/" className="flex items-center">
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              Market Prediction
            </span>
          </Link>

          {/* Right side */}
          <div className="flex items-center gap-4">
            {isLoading ? (
              <div className="text-sm text-gray-500">Loading...</div>
            ) : isAuthenticated && user ? (
              <>
                {/* User info */}
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {user.name || user.email}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {user.balance.toLocaleString()} pts
                    </p>
                  </div>
                  {/* Role badge */}
                  {user.role !== "user" && (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {user.role}
                    </span>
                  )}
                </div>

                {/* Logout button */}
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

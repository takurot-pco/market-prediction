"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loginWithCallback, error, isLoading } = useAuthStore();
  const processedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");

    if (!code) {
      router.push("/login");
      return;
    }

    // Prevent double processing in React Strict Mode
    if (processedRef.current) {
      return;
    }
    processedRef.current = true;

    const handleCallback = async () => {
      try {
        await loginWithCallback(code);
        router.push("/");
      } catch {
        // Error is stored in state, will be displayed
        router.push("/login");
      }
    };

    handleCallback();
  }, [searchParams, loginWithCallback, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        {error ? (
          <div className="text-red-600 dark:text-red-400">
            <p className="text-lg font-medium mb-2">Authentication Error</p>
            <p className="text-sm">{error}</p>
            <p className="text-sm mt-4">Redirecting to login...</p>
          </div>
        ) : isLoading ? (
          <div className="flex flex-col items-center gap-4">
            <svg
              className="animate-spin h-10 w-10 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-gray-600 dark:text-gray-400">
              Authenticating...
            </p>
          </div>
        ) : (
          <p className="text-gray-600 dark:text-gray-400">
            Processing...
          </p>
        )}
      </div>
    </main>
  );
}

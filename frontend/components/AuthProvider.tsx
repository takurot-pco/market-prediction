"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store/auth";

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { token, fetchUser } = useAuthStore();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initialize = async () => {
      if (token) {
        await fetchUser();
      }
      setIsInitialized(true);
    };

    initialize();
  }, [token, fetchUser]);

  // Show nothing while hydrating to prevent flash
  if (!isInitialized) {
    return null;
  }

  return <>{children}</>;
}

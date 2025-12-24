"use client";

import { useAuthStore } from "@/lib/store/auth";
import type { UserRole } from "@/types/auth";
import { hasRequiredRole } from "@/types/auth";

interface RoleGateProps {
  /**
   * The minimum role required to view the children.
   */
  requiredRole: UserRole;
  /**
   * Content to show if user has required role.
   */
  children: React.ReactNode;
  /**
   * Optional fallback content if user doesn't have required role.
   */
  fallback?: React.ReactNode;
}

/**
 * Component that conditionally renders children based on user role.
 * Uses role hierarchy: admin > moderator > user.
 *
 * @example
 * // Only show to moderators and admins
 * <RoleGate requiredRole="moderator">
 *   <AdminPanel />
 * </RoleGate>
 *
 * @example
 * // Show different content based on role
 * <RoleGate requiredRole="admin" fallback={<p>Access denied</p>}>
 *   <AdminSettings />
 * </RoleGate>
 */
export function RoleGate({ requiredRole, children, fallback = null }: RoleGateProps) {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return <>{fallback}</>;
  }

  if (!hasRequiredRole(user.role, requiredRole)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Hook to check if current user has required role.
 */
export function useHasRole(requiredRole: UserRole): boolean {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return false;
  }

  return hasRequiredRole(user.role, requiredRole);
}

/**
 * Hook to check if current user is at least a moderator.
 */
export function useIsModerator(): boolean {
  return useHasRole("moderator");
}

/**
 * Hook to check if current user is an admin.
 */
export function useIsAdmin(): boolean {
  return useHasRole("admin");
}

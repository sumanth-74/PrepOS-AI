import type { AppRole } from "@/lib/types/api";

const ROLE_ALIASES: Record<string, AppRole> = {
  student: "student",
  faculty: "faculty",
  institute_admin: "institute_admin",
  super_admin: "super_admin",
};

export function normalizeRoles(rawRoles: string[]): AppRole[] {
  return rawRoles
    .map((role) => ROLE_ALIASES[role.toLowerCase()] ?? null)
    .filter((role): role is AppRole => role !== null);
}

export function hasAnyRole(roles: AppRole[], allowed: AppRole[]): boolean {
  return allowed.some((role) => roles.includes(role));
}

export function defaultPortalPath(roles: AppRole[]): string {
  if (hasAnyRole(roles, ["faculty", "institute_admin", "super_admin"])) {
    return "/mentor/dashboard";
  }
  return "/student/dashboard";
}

export function isMentorRole(roles: AppRole[]): boolean {
  return hasAnyRole(roles, ["faculty", "institute_admin", "super_admin"]);
}

export function isStudentRole(roles: AppRole[]): boolean {
  return roles.includes("student");
}

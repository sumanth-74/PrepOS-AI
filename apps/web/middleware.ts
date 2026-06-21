import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import {
  isAuthedFromCookie,
  readRolesFromCookie,
} from "@/lib/auth/session-cookie";
import { hasAnyRole } from "@/lib/auth/roles";
import type { AppRole } from "@/lib/types/api";

const PUBLIC_PATHS = ["/login", "/register", "/unauthorized"];

function isPublicPath(pathname: string): boolean {
  return (
    PUBLIC_PATHS.includes(pathname) ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon")
  );
}

function redirect(request: NextRequest, pathname: string): NextResponse {
  return NextResponse.redirect(new URL(pathname, request.url));
}

function guardRoute(
  roles: AppRole[],
  allowed: AppRole[],
  request: NextRequest,
): NextResponse | null {
  if (!hasAnyRole(roles, allowed)) {
    return redirect(request, "/unauthorized");
  }
  return null;
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  if (isPublicPath(pathname) || pathname === "/") {
    return NextResponse.next();
  }

  const cookieHeader = request.headers.get("cookie") ?? undefined;
  const authed = isAuthedFromCookie(cookieHeader);
  const roles = readRolesFromCookie(cookieHeader);

  if (!authed) {
    return redirect(request, "/login");
  }

  if (pathname.startsWith("/student")) {
    const denied = guardRoute(roles, ["student"], request);
    if (denied) return denied;
  }

  if (pathname.startsWith("/mentor")) {
    const denied = guardRoute(
      roles,
      ["faculty", "institute_admin", "super_admin"],
      request,
    );
    if (denied) return denied;
  }

  if (pathname.startsWith("/faculty")) {
    const denied = guardRoute(
      roles,
      ["faculty", "institute_admin", "super_admin"],
      request,
    );
    if (denied) return denied;
  }

  if (pathname.startsWith("/admin")) {
    const denied = guardRoute(roles, ["institute_admin", "super_admin"], request);
    if (denied) return denied;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\..*).*)"],
};

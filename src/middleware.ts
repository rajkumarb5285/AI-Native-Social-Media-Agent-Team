import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE_NAME = "nexus_session";

// Protected application routes that strictly require an authenticated session
const PROTECTED_PREFIXES = ["/studio", "/connect", "/review", "/onboarding"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
  const isAuthenticated = Boolean(sessionCookie?.value);

  // If visiting /login while already authenticated, redirect to /studio
  if (pathname === "/login") {
    if (isAuthenticated) {
      const returnTo = request.nextUrl.searchParams.get("return_to");
      const destination = returnTo && returnTo.startsWith("/") && !returnTo.startsWith("//") ? returnTo : "/studio";
      return NextResponse.redirect(new URL(destination, request.url));
    }
    return NextResponse.next();
  }

  // Check if route is protected
  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );

  if (isProtected && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    // Sanitize return_to as same-origin relative path
    const safeReturnTo = pathname.startsWith("/") && !pathname.startsWith("//") ? pathname : "/studio";
    loginUrl.searchParams.set("return_to", safeReturnTo);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - api routes (handled by backend or rewrite)
     * - auth routes (OAuth callback/login)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, fonts, etc.)
     */
    "/((?!api|auth|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};

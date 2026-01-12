import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // --- 1. EXCLUSIONS (Public Paths) ---
    // We explicitly check for paths that should NOT be protected.
    // This includes static files, next internals, login page, and api/auth.

    // Check for Next.js internals and static assets
    if (
        pathname.startsWith('/_next') ||
        pathname.startsWith('/static') ||
        pathname.includes('.') // Any file with extension (css, png, ico, json, etc)
    ) {
        return NextResponse.next();
    }

    // Check for Login and Auth API
    if (
        pathname.startsWith('/login') ||
        pathname.startsWith('/api/auth')
    ) {
        // Special Case: Redirect logged-in users away from /login to /
        if (pathname === '/login' && request.cookies.has('auth_session')) {
            return NextResponse.redirect(new URL('/', request.url));
        }
        return NextResponse.next();
    }

    // Check for Public Data (explicitly allow data folder if not caught by extension check)
    if (pathname.startsWith('/data')) {
        return NextResponse.next();
    }

    // --- 2. PROTECTION (Auth Check) ---
    const hasAuth = request.cookies.has('auth_session');

    if (!hasAuth) {
        // console.log(`[Middleware] Blocking access to ${pathname} -> Redirecting to /login`);
        const loginUrl = new URL('/login', request.url);
        loginUrl.searchParams.set('from', pathname);
        return NextResponse.redirect(loginUrl);
    }

    // Access Granted
    return NextResponse.next();
}

// Run on everything to ensure our custom logic handles it all safely.
export const config = {
    matcher: '/:path*',
};

import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { username, password } = body;

        // Hardcoded Credentials
        const VALID_USER = 'mulimen';
        const VALID_PASS = 'c_EW_jlFeWiCere4';

        if (username === VALID_USER && password === VALID_PASS) {
            // Create response
            const response = NextResponse.json({ success: true });

            // Set Cookie
            // HttpOnly: Not accessible via JS (secure)
            // Secure: Send only over HTTPS (on localhost sometimes this is lax, but standard is secure)
            // SameSite: Strict (CSRF protection)
            // MaxAge: 7 days
            response.cookies.set('auth_session', 'true', {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'lax', // Use Lax for better compatibility with redirects
                path: '/',
                maxAge: 60 * 60 * 24 * 7 // 7 days
            });

            return response;
        } else {
            return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
        }

    } catch (_error) {
        return NextResponse.json({ error: 'Internal Error' }, { status: 500 });
    }
}

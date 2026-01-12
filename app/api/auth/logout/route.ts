import { NextResponse } from 'next/server';

export async function POST(_request: Request) {
    // Create response (redirect to login or JSON success)
    // We'll return JSON success so frontend can handle redirect
    const response = NextResponse.json({ success: true });

    // Clear Cookie
    response.cookies.set('auth_session', '', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        path: '/',
        maxAge: 0 // Expire immediately
    });

    return response;
}

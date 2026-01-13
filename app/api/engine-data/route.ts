import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const file = searchParams.get('file'); // supports: state | history | engine_state.json

    const BASE_URL = process.env.BACKEND_REPO_RAW_URL;

    if (!BASE_URL) {
        return NextResponse.json(
            { error: 'Configuration Error: BACKEND_REPO_RAW_URL not set' },
            { status: 500 }
        );
    }

    let targetUrl: string | null = null;

    // 🔧 ACCEPT BOTH OLD + NEW CALL STYLES
    if (file === 'state' || file === 'engine_state.json') {
        targetUrl = `${BASE_URL}/engine_state.json`;
    } else if (file === 'history' || file === 'backtest_results.json') {
        targetUrl = `${BASE_URL}/backtest_results.json`;
    } else {
        return NextResponse.json(
            { error: 'Invalid file type requested' },
            { status: 400 }
        );
    }

    const upstreamUrl = `${targetUrl}?t=${Date.now()}`;

    try {
        const res = await fetch(upstreamUrl, { cache: 'no-store' });

        if (!res.ok) {
            return NextResponse.json(
                { error: `Failed to fetch backend file (${res.status})` },
                { status: res.status }
            );
        }

        const data = await res.json();

        return NextResponse.json(data, {
            headers: {
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        });

    } catch (err) {
        return NextResponse.json(
            { error: 'Internal Server Error fetching data' },
            { status: 500 }
        );
    }
}

import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const file = searchParams.get('file'); // supports: state | history | engine_state.json

    // URL of the folder where 'engine_state.json' and 'backtest_results.json' are synced.
    // Set this in Railway Variables.
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
        targetUrl = `${BASE_URL}/state/engine_state.json`;
    } else if (file === 'history' || file === 'backtest_results.json') {
        targetUrl = `${BASE_URL}/data/backtest_results.json`;
    } else {
        return NextResponse.json(
            { error: 'Invalid file type requested' },
            { status: 400 }
        );
    }

    const upstreamUrl = `${targetUrl}?t=${Date.now()}`;
    const token = process.env.GITHUB_PAT;

    try {
        const headers: HeadersInit = {
            'Cache-Control': 'no-cache'
        };

        if (token) {
            headers['Authorization'] = `token ${token}`;
        }

        const res = await fetch(upstreamUrl, {
            headers: headers,
            cache: 'no-store'
        });

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

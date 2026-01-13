import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const fileType = searchParams.get('file'); // 'state' or 'history'

    // Default to a placeholder if Env Var is missing (safe failover)
    // The user MUST set this in Railway.
    // Format: https://raw.githubusercontent.com/USER/REPO/BRANCH
    const BASE_URL = process.env.BACKEND_REPO_RAW_URL;

    if (!BASE_URL) {
        return NextResponse.json({
            error: "Configuration Error: BACKEND_REPO_RAW_URL not set in environment variables."
        }, { status: 500 });
    }

    let targetUrl = "";

    if (fileType === 'state') {
        targetUrl = `${BASE_URL}/state/engine_state.json`;
    } else if (fileType === 'history') {
        // NOTE: This assumes backtest_results.json is synced to 'data/' folder in backend repo.
        // If not, this might fail until backend v11 is deployed.
        targetUrl = `${BASE_URL}/data/backtest_results.json`;
    } else {
        return NextResponse.json({ error: "Invalid file type requested" }, { status: 400 });
    }

    // Add Cache Busting to the Upstream Request
    const upstreamUrl = `${targetUrl}?t=${new Date().getTime()}`;

    try {
        console.log(`[Proxy] Fetching: ${upstreamUrl}`);
        const res = await fetch(upstreamUrl, { cache: 'no-store' });

        if (!res.ok) {
            console.error(`[Proxy] Failed to fetch ${upstreamUrl}: ${res.status}`);
            return NextResponse.json({
                error: `Failed to fetch data from backend storage (${res.status})`,
                details: "Check BACKEND_REPO_RAW_URL and ensure files exist in the repo."
            }, { status: res.status });
        }

        const data = await res.json();

        // Return with cache-control headers to prevent Vercel/Railway edge caching
        return NextResponse.json(data, {
            headers: {
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        });

    } catch (error) {
        console.error("[Proxy] Exception:", error);
        return NextResponse.json({ error: "Internal Server Error fetching data" }, { status: 500 });
    }
}

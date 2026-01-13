import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const file = searchParams.get('file'); // supports: state | history | engine_state.json

    // STRATEGY: 
    // 1. If Development (Localhost), try to read directly from sibling folder (../titan_hammer)
    // 2. If Production (Railway) or local fallback fails, use GitHub Raw Proxy (requires Token)

    const isDev = process.env.NODE_ENV === 'development';

    // --- LOCAL FILE SYSTEM FALLBACK (FOR LOCALHOST NO-CONFIG) ---
    if (isDev) {
        try {
            let localPath = "";
            const projectRoot = process.cwd(); // i:\INVIS SPY\invis-web

            if (file === 'state' || file === 'engine_state.json') {
                localPath = path.resolve(projectRoot, '../titan_hammer/state/engine_state.json');
            } else if (file === 'history' || file === 'backtest_results.json') {
                // Try 'data' folder first (v11), then 'invis-web/public/data' (legacy)
                localPath = path.resolve(projectRoot, '../titan_hammer/data/backtest_results.json');
                if (!fs.existsSync(localPath)) {
                    localPath = path.resolve(projectRoot, 'public/data/backtest_results.json');
                }
            }

            if (localPath && fs.existsSync(localPath)) {
                const fileContent = fs.readFileSync(localPath, 'utf-8');
                const data = JSON.parse(fileContent);
                console.log(`[Local Mode] Served ${file} from disk: ${localPath}`);
                return NextResponse.json(data);
            }
        } catch (localErr) {
            console.warn("[Local Mode] Failed to read local file, falling back to Proxy:", localErr);
        }
    }

    // --- REMOTE PROXY FALLBACK (FOR RAILWAY / PROD) ---
    // URL of the folder where 'engine_state.json' and 'backtest_results.json' are synced.
    const BASE_URL = process.env.BACKEND_REPO_RAW_URL;

    // In PROD, if this is missing, we must fail.
    // In DEV, if we reached here, it means local file didn't work AND config is missing.
    if (!BASE_URL) {
        return NextResponse.json(
            { error: 'Configuration Error: BACKEND_REPO_RAW_URL not set (and local file not found)' },
            { status: 500 }
        );
    }

    let targetUrl: string | null = null;

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

import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

export async function GET() {
    try {
        // Path to engine state file (titan_hammer/state/engine_state.json)
        // Adjust relative path based on where this route is (app/api/engine/state/route.ts)
        // route.ts -> state -> engine -> api -> app -> invis-web -> INVIS SPY -> titan_hammer

        // Simpler: process.cwd() is usually the root of the Next.js project (invis-web)
        // so we go up one level to INVIS SPY, then down to titan_hammer

        const statePath = path.resolve(process.cwd(), '..', 'titan_hammer', 'state', 'engine_state.json');

        try {
            const data = await fs.readFile(statePath, 'utf8');
            const state = JSON.parse(data);
            return NextResponse.json(state);
        } catch (fileError) {
            console.error("State File Read Error:", fileError);
            // If file doesn't exist, return a default "safe" state
            return NextResponse.json({
                state: "UNKNOWN",
                equity: 0,
                ath: 0,
                drawdown: 0,
                notes: "State file not found or unreadable."
            });
        }

    } catch (error) {
        console.error("API Error:", error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}

import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { action } = body;

        if (!action || (action !== 'PAUSE' && action !== 'RESUME')) {
            return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
        }

        // Determine flag based on action
        const flag = action === 'PAUSE' ? '--pause' : '--resume';

        // Path to python script
        // Assuming we are running from web/ directory, scripts is in ../titan_hammer/scripts
        // Adjust absolute path logic for Windows safety
        const scriptPath = path.resolve(process.cwd(), '..', 'titan_hammer', 'scripts', 'pause_control.py');

        const command = `python "${scriptPath}" ${flag}`;

        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error(`exec error: ${error}`);
                    resolve(NextResponse.json({ error: 'Failed to execute control script', details: stderr }, { status: 500 }));
                    return;
                }

                console.log(`stdout: ${stdout}`);
                resolve(NextResponse.json({ success: true, message: `Engine ${action} executed`, output: stdout }));
            });
        });

    } catch (error) {
        console.error("API Error:", error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}

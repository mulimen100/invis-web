'use client';
/* eslint-disable react-hooks/exhaustive-deps */

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ArenaPage() {
    const [timeLeft, setTimeLeft] = useState<string>("");
    const [chartData, setChartData] = useState<any[]>([]);

    useEffect(() => {
        fetch('/data/backtest_results.json')
            .then(res => res.json())
            .then(data => {
                // Optimize: Limit points if too heavy? For now, full history is requested.
                // Or maybe slice last 5 years? User said "over time... years following".
                // Full history might be heavy for Recharts Canvas but let's try.
                // Decimation might be needed later.
                // We keep only necessary fields to save memory if possible?
                setChartData(data.history);
            })
            .catch(err => console.error("Failed to load chart data", err));
    }, []);

    // Log Data Mock
    const logs = [
        { time: "13:16:51", level: "INFO", message: "Initializing neural weights..." },
        { time: "13:16:51", level: "SUCCESS", message: "Connected to market data stream." },
        { time: "13:16:51", level: "INFO", message: "Calculating regime volatility..." },
        { time: "13:16:51", level: "ANALYSIS", message: "Regime detected: RISK_ON_FULL", highlight: "text-purple-400" },
        { time: "13:16:51", level: "INFO", message: "Rebalancing portfolio..." },
        { time: "13:16:51", level: "READY", message: "Waiting for next tick.", highlight: "text-green-400 animate-pulse" }
    ];

    useEffect(() => {
        // Timer Logic
        const calculateTimeLeft = () => {
            const now = new Date();
            const target = new Date();
            target.setHours(23, 0, 0, 0);

            if (now > target) {
                target.setDate(target.getDate() + 1);
            }

            const diff = target.getTime() - now.getTime();

            const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const minutes = Math.floor((diff / 1000 / 60) % 60);
            const seconds = Math.floor((diff / 1000) % 60);

            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        };

        const timer = setInterval(() => {
            setTimeLeft(calculateTimeLeft());
        }, 1000);

        setTimeLeft(calculateTimeLeft()); // Initial call

        return () => clearInterval(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="container mx-auto px-6 py-12">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-2">The Arena</h1>
                    <p className="text-gray-400">Live Engine Performance Monitoring</p>
                </div>

                <div className="flex items-center gap-6">
                    {/* Manual Override Controls */}
                    <div className="flex gap-2">
                        <ManualControlButton action="RESUME" label="RESUME ENGINE" color="bg-green-600 hover:bg-green-500" />
                        <ManualControlButton action="PAUSE" label="PAUSE ENGINE" color="bg-red-600 hover:bg-red-500" />
                    </div>

                    {/* Countdown Timer */}
                    <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col items-center">
                        <div className="text-xs text-blue-400 font-mono mb-1">NEXT ENGINE RUN</div>
                        <div className="text-3xl font-mono font-bold text-white tracking-widest shadow-blue-500/20 drop-shadow-lg">
                            {timeLeft}
                        </div>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-green-500/30 bg-green-500/10 text-green-400 text-sm font-mono animate-pulse">
                        <span className="w-2 h-2 rounded-full bg-green-400" />
                        LIVE CONNECTION
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* SPY Bot Card */}
                <div className="rounded-3xl border border-white/10 bg-white/5 p-8 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-32 bg-blue-600/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-blue-600/20 transition-all duration-500" />

                    <div className="flex justify-between items-start mb-8 relative">
                        <div>
                            <h2 className="text-3xl font-bold">SPY</h2>
                            <span className="text-blue-400 text-sm tracking-wider font-mono">TITAN HAMMER</span>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-mono font-bold text-white">₪100,000</div>
                            <div className="text-gray-400 text-sm">0.00%</div>
                        </div>
                    </div>

                    <div className="space-y-4 relative">
                        <div className="flex justify-between text-sm border-b border-white/5 pb-2">
                            <span className="text-gray-500">Status</span>
                            <span className="text-green-400 font-mono">ACTIVE (3X)</span>
                        </div>
                        <div className="flex justify-between text-sm border-b border-white/5 pb-2">
                            <span className="text-gray-500">Today</span>
                            <span className="text-white font-mono">0.00%</span>
                        </div>
                        <div className="flex justify-between text-sm pb-2">
                            <span className="text-gray-500">Drawdown</span>
                            <span className="text-white font-mono">0.00%</span>
                        </div>
                    </div>
                </div>

                {/* Engine Output Log */}
                <div className="lg:col-span-2 rounded-3xl border border-white/10 bg-black/40 backdrop-blur-md p-8 relative overflow-hidden flex flex-col">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                            ENGINE OUTPUT LOG
                        </h2>
                        <span className="text-xs font-mono text-gray-500">T-MINUS 1 SECOND LATENCY</span>
                    </div>

                    <div className="flex-1 font-mono text-xs md:text-sm space-y-3 overflow-y-auto max-h-[250px] custom-scrollbar pr-2">
                        {logs.map((log, idx) => (
                            <div key={idx} className="flex gap-4 border-l-2 border-white/5 pl-4 hover:border-blue-500/50 transition-colors group">
                                <span className="text-gray-500">[{log.time}]</span>
                                <span className={`font-bold w-20 text-right ${log.level === 'INFO' ? 'text-blue-400' :
                                    log.level === 'SUCCESS' ? 'text-green-400' :
                                        log.level === 'ANALYSIS' ? 'text-purple-400' :
                                            log.level === 'READY' ? 'text-green-300' : 'text-gray-300'
                                    }`}>{log.level}</span>
                                <span className={`text-gray-300 ${log.highlight || ''}`}>{log.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Performance Graph */}
            <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-8 relative overflow-hidden backdrop-blur-sm">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">Long-Term Performance</h2>
                        <span className="text-gray-400 text-sm">Titan Engine vs S&P 500 (2025-2040)</span>
                    </div>
                    {chartData.length > 0 && (
                        <div className="flex gap-4 text-xs font-mono">
                            <span className="text-green-400">TITAN: ${chartData[chartData.length - 1].titan.toLocaleString()}</span>
                            <span className="text-gray-400">INDEX: ${chartData[chartData.length - 1].spy.toLocaleString()}</span>
                        </div>
                    )}
                </div>

                <div className="h-[400px] w-full">
                    {chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#555"
                                    tickFormatter={(val) => new Date(val).getFullYear().toString()}
                                    minTickGap={50}
                                    style={{ fontSize: '12px' }}
                                />
                                <YAxis
                                    stroke="#555"
                                    tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                                    scale="log"
                                    domain={['auto', 'auto']}
                                    style={{ fontSize: '12px' }}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#000', borderColor: '#333' }}
                                    formatter={(value: any) => [`$${value.toLocaleString()}`, '']}
                                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                />
                                <Line type="monotone" dataKey="titan" stroke="#4ade80" strokeWidth={2} dot={false} name="Titan Engine" />
                                <Line type="monotone" dataKey="spy" stroke="#64748b" strokeWidth={2} dot={false} name="S&P 500" />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500 animate-pulse">
                            Loading Historical Data...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function ManualControlButton({ action, label, color }: { action: 'PAUSE' | 'RESUME', label: string, color: string }) {
    const [loading, setLoading] = useState(false);

    const handleClick = async () => {
        if (!confirm(`Are you sure you want to ${action} the engine?`)) return;

        setLoading(true);
        try {
            const res = await fetch('/api/engine/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await res.json();
            if (data.success) {
                alert(`SUCCESS: Engine ${action} command sent.`);
            } else {
                alert(`ERROR: ${data.error}`);
            }
        } catch (e) {
            console.error(e);
            alert("Failed to communicate with engine.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={loading}
            className={`${color} text-white font-bold text-xs px-4 py-3 rounded-lg shadow-lg hover:opcaity-90 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
            {loading ? 'PROCESSING...' : label}
        </button>
    );
}

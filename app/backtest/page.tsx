'use client';

import React, { useEffect, useState, useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceDot,
    ReferenceArea
} from 'recharts';

interface SimEvent {
    Date: string;
    Type: string;
    Equity: number;
    Info: string;
}

interface Milestone {
    Year: number;
    Date: string;
    SPY: number;
    Titan: number;
    Delta: number;
}

interface SimDataPoint {
    date: string;
    spy: number;
    titan: number;
    state: string;
    event: string | null;
}

interface BacktestData {
    metadata: {
        period: string;
        years: number;
        initial_investment: number;
    };
    stats: {
        spy_final: number;
        titan_final: number;
        spy_cagr: number;
        titan_cagr: number;
    };
    milestones: Record<string, Milestone>;
    events: SimEvent[];
    history: SimDataPoint[];
}

export default function BacktestPage() {
    const [data, setData] = useState<BacktestData | null>(null);

    useEffect(() => {
        fetch('/data/backtest_results.json')
            .then((res) => res.json())
            .then((d) => setData(d))
            .catch((err) => console.error('Failed to load backtest data', err));
    }, []);

    if (!data) {
        return (
            <div className="min-h-screen bg-[#020617] flex items-center justify-center text-white">
                <div className="animate-pulse text-xl font-mono text-cyan-400">LOADING SIMULATION CORE...</div>
            </div>
        );
    }

    // Calculate Yearly Data for Table
    const yearlyData = [];
    if (data.history.length > 0) {
        let currentYear = new Date(data.history[0].date).getFullYear();
        let startEquitySpy = data.metadata.initial_investment;
        let startEquityTitan = data.metadata.initial_investment;

        // We need to find the first entry of each year to calc returns
        // Or just take end of year values.
        // Let's iterate history to grab end-of-year snapshots.
        const history = data.history;
        for (let i = 0; i < history.length; i++) {
            const d = new Date(history[i].date);
            if (d.getFullYear() !== currentYear || i === history.length - 1) {
                // End of previous year (or actual end of data)
                const snapshot = history[i === history.length - 1 ? i : i - 1];
                yearlyData.push({
                    year: currentYear,
                    spy: snapshot.spy,
                    titan: snapshot.titan,
                    titan_vs_spy: ((snapshot.titan - snapshot.spy) / snapshot.spy) * 100
                });
                currentYear = d.getFullYear();
            }
        }
    }


    // Optimize: Downsample chart data for performance
    const chartData = useMemo(() => {
        if (!data || !data.history) return [];
        const history = data.history;
        const MAX_POINTS = 500;

        if (history.length <= MAX_POINTS) return history;

        const step = Math.ceil(history.length / MAX_POINTS);
        return history.filter((_: any, index: number) => index % step === 0 || index === history.length - 1);
    }, [data]);

    return (
        <div className="min-h-screen bg-[#020617] text-gray-100 p-8 font-sans">
            <div className="max-w-7xl mx-auto space-y-12">

                {/* Header */}
                <div className="text-center space-y-4">
                    <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-500 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]">
                        AUTHENTIC WALK-FORWARD
                    </h1>
                    <p className="text-gray-400 uppercase tracking-widest text-sm font-medium">
                        20-Year Unseen Market Simulation • Initial Capital: ${data.metadata.initial_investment.toLocaleString()}
                    </p>
                </div>

                {/* Summary Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card label="TITAN FINAL EQUITY" value={`$${data.stats.titan_final.toLocaleString()}`} color="text-green-400" />
                    <Card label="SPY FINAL EQUITY" value={`$${data.stats.spy_final.toLocaleString()}`} color="text-gray-300" />
                    <Card label="TITAN CAGR" value={`${data.stats.titan_cagr}%`} color="text-cyan-400" />
                    <Card label="SPY CAGR" value={`${data.stats.spy_cagr}%`} color="text-gray-400" />
                </div>

                {/* MAIN CHART */}
                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm shadow-2xl">
                    <h2 className="text-xl font-bold mb-6 text-white tracking-tight flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                        EQUITY CURVE SIMULATION
                    </h2>
                    <div className="h-[500px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#666"
                                    tickFormatter={(str) => new Date(str).getFullYear().toString()}
                                    minTickGap={50}
                                />
                                <YAxis
                                    stroke="#666"
                                    tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                                    domain={['auto', 'auto']}
                                    scale="log"
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                                    itemStyle={{ fontSize: '12px' }}
                                    labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                                    formatter={(value: any) => [`$${value?.toLocaleString()}`, '']}
                                />
                                <Legend iconType="circle" />

                                <Line
                                    type="monotone"
                                    dataKey="spy"
                                    stroke="#9ca3af"
                                    strokeWidth={2}
                                    dot={false}
                                    name="S&P 500 Index"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="titan"
                                    stroke="#22d3ee"
                                    strokeWidth={2}
                                    dot={false}
                                    name="TITAN ENGINE"
                                />

                                {/* Event Markers (Pause/Resume) */}
                                {data.events.map((e, i) => (
                                    e.Type === "PAUSE" ? (
                                        <ReferenceDot
                                            key={i}
                                            x={e.Date}
                                            y={e.Equity}
                                            r={4}
                                            fill="#ef4444"
                                            stroke="none"
                                        />
                                    ) : (
                                        <ReferenceDot
                                            key={i}
                                            x={e.Date}
                                            y={e.Equity}
                                            r={4}
                                            fill="#4ade80"
                                            stroke="none"
                                        />
                                    )
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 flex gap-6 justify-center text-xs text-gray-400">
                        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500"></span> ENGINE PAUSE</div>
                        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-400"></span> ENGINE RESUME</div>
                    </div>
                </div>

                {/* Milestone Table */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                        <h3 className="text-xl font-bold mb-4 text-white">MILESTONE CHECKPOINTS</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead>
                                    <tr className="border-b border-white/10 text-gray-400">
                                        <th className="pb-3 font-semibold">TIMEFRAME</th>
                                        <th className="pb-3 font-semibold text-right">INDEX VALUE</th>
                                        <th className="pb-3 font-semibold text-right text-cyan-400">ENGINE VALUE</th>
                                        <th className="pb-3 font-semibold text-right">DIFFERENCE</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {[5, 10, 15, 20].map((year) => {
                                        const m = data.milestones[year.toString()];
                                        if (!m) return null;
                                        return (
                                            <tr key={year} className="group hover:bg-white/5 transition-colors">
                                                <td className="py-4 text-gray-300 font-medium">{year} YEARS</td>
                                                <td className="py-4 text-right text-gray-400">${m.SPY.toLocaleString()}</td>
                                                <td className="py-4 text-right text-cyan-400 font-bold">${m.Titan.toLocaleString()}</td>
                                                <td className="py-4 text-right text-green-400">
                                                    +${(m.Titan - m.SPY).toLocaleString()}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Event Log */}
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                        <h3 className="text-xl font-bold mb-4 text-white">ENGINE EVENT LOG</h3>
                        <div className="overflow-y-auto max-h-[300px] space-y-2 pr-2 custom-scrollbar">
                            {data.events.slice().reverse().map((e, i) => (
                                <div key={i} className={`p-3 rounded-lg border ${e.Type === 'PAUSE' ? 'border-red-500/20 bg-red-500/10' : 'border-green-500/20 bg-green-500/10'} flex justify-between items-center`}>
                                    <div>
                                        <div className={`text-xs font-bold ${e.Type === 'PAUSE' ? 'text-red-400' : 'text-green-400'}`}>
                                            {e.Type} PROTOCOL
                                        </div>
                                        <div className="text-xs text-gray-400">{e.Date}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm font-medium text-white">${e.Equity.toLocaleString()}</div>
                                        <div className="text-[10px] text-gray-500 uppercase">{e.Info}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* FULL YEARLY BREAKDOWN */}
                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                    <h3 className="text-xl font-bold mb-4 text-white">YEARLY PERFORMANCE BREAKDOWN</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="border-b border-white/10 text-gray-400">
                                    <th className="pb-3 font-semibold">YEAR</th>
                                    <th className="pb-3 font-semibold text-right">INDEX EQUITY</th>
                                    <th className="pb-3 font-semibold text-right text-cyan-400">TITAN EQUITY</th>
                                    <th className="pb-3 font-semibold text-right">OUTPERFORMANCE</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {yearlyData.map((row) => (
                                    <tr key={row.year} className="hover:bg-white/5 transition-colors">
                                        <td className="py-3 text-gray-300">{row.year}</td>
                                        <td className="py-3 text-right text-gray-400">${row.spy.toLocaleString()}</td>
                                        <td className="py-3 text-right text-cyan-400 font-mono">${row.titan.toLocaleString()}</td>
                                        <td className={`py-3 text-right font-medium ${row.titan_vs_spy >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {row.titan_vs_spy > 0 ? '+' : ''}{row.titan_vs_spy.toFixed(1)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
}

function Card({ label, value, color }: { label: string, value: string, color: string }) {
    return (
        <div className="bg-[#0f172a]/50 p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all hover:bg-[#0f172a]">
            <div className="text-xs font-semibold text-gray-500 mb-1 tracking-wider">{label}</div>
            <div className={`text-2xl lg:text-3xl font-bold tracking-tight ${color}`}>{value}</div>
        </div>
    );
}

'use client';

import { useState, useEffect } from 'react';

interface MarketFlag {
    date: string;
    return: number;
    flag: 'GREEN' | 'YELLOW' | 'RED';
}

interface FlagData {
    updated: string;
    count: number;
    flags: MarketFlag[];
}

export default function InsightsPage() {
    const [data, setData] = useState<FlagData | null>(null);
    const [timeLeft, setTimeLeft] = useState<string>("");

    useEffect(() => {
        fetch('/data/market_flags.json')
            .then(res => res.json())
            .then(data => setData(data))
            .catch(err => console.error("Failed to load market flags:", err));

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
    }, []);

    const getFlagColor = (flag: string) => {
        switch (flag) {
            case 'GREEN': return 'bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.4)]';
            case 'YELLOW': return 'bg-yellow-500 shadow-[0_0_15px_rgba(234,179,8,0.4)]';
            case 'RED': return 'bg-red-600 shadow-[0_0_15px_rgba(220,38,38,0.6)] animate-pulse';
            default: return 'bg-gray-500';
        }
    };

    const formatDateShort = (dateStr: string) => {
        const date = new Date(dateStr);
        return `${date.getDate()}/${date.getMonth() + 1}`;
    };

    return (
        <div className="container mx-auto px-6 py-12">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12">
                <div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-2 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Market Insights
                    </h1>
                    <p className="text-gray-400 text-lg border-l-2 border-blue-500 pl-4 w-fit">
                        Deep analysis and signals from the Titan Engines.
                    </p>
                </div>

                {/* Countdown Timer */}
                <div className="mt-6 md:mt-0 bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col items-center">
                    <div className="text-xs text-blue-400 font-mono mb-1">NEXT ENGINE RUN</div>
                    <div className="text-3xl font-mono font-bold text-white tracking-widest shadow-blue-500/20 drop-shadow-lg">
                        {timeLeft}
                    </div>
                </div>
            </div>

            {/* Market Pulse Section */}
            <div className="mb-16">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white">Market Pulse (Last 30 Days)</h2>
                    {data && (
                        <span className="text-xs text-gray-500 font-mono">
                            UPDATED: {new Date(data.updated).toLocaleString()}
                        </span>
                    )}
                </div>

                {!data ? (
                    <div className="h-24 rounded-2xl border border-white/5 bg-white/5 animate-pulse flex items-center justify-center text-gray-500">
                        Loading Market Signals...
                    </div>
                ) : (
                    <div className="bg-black/40 backdrop-blur-md rounded-2xl border border-white/10 p-8 relative overflow-hidden">
                        {/* Background Decoration */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

                        {/* Grid Container - 3 Rows of 10 */}
                        <div className="flex justify-center w-full">
                            <div className="grid grid-cols-5 md:grid-cols-10 gap-x-4 gap-y-8 md:gap-x-8 md:gap-y-10">
                                {/* Render last 30 flags */}
                                {data.flags.slice(-30).map((item, idx) => (
                                    <div key={idx} className="group flex flex-col items-center gap-3">

                                        {/* The Circle Flag */}
                                        <div className={`w-6 h-6 md:w-8 md:h-8 rounded-full transition-all duration-300 group-hover:scale-110 ${getFlagColor(item.flag)} relative`}>
                                            {/* Tooltip on Hover */}
                                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20 whitespace-nowrap">
                                                <div className="bg-gray-900 border border-white/10 px-3 py-2 rounded-lg shadow-2xl">
                                                    <div className="text-sm font-bold text-white mb-1">{item.date}</div>
                                                    <div className={`text-xs font-mono font-bold ${item.return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                        Change: {(item.return * 100).toFixed(2)}%
                                                    </div>
                                                </div>
                                                <div className="w-2 h-2 bg-gray-900 border-r border-b border-white/10 rotate-45 absolute -bottom-1 left-1/2 -translate-x-1/2"></div>
                                            </div>
                                        </div>

                                        {/* Date Label */}
                                        <div className="text-[10px] md:text-xs font-mono text-gray-500 group-hover:text-gray-300 transition-colors">
                                            {formatDateShort(item.date)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="mt-8 flex gap-6 justify-center md:justify-start text-xs text-gray-500 font-mono border-t border-white/5 pt-6">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]"></div>
                                <span>STABLE / UP</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.4)]"></div>
                                <span>DECLINE</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-red-600 shadow-[0_0_10px_rgba(220,38,38,0.6)]"></div>
                                <span>SHARP DROP (&lt;-1.5%)</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

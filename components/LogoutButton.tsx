'use client';

import { useState } from 'react';

export default function LogoutButton() {
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        setLoading(true);
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            // Force hard navigation to clear any client-side state/cache
            window.location.href = '/login';
        } catch (e) {
            console.error("Logout failed", e);
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handleLogout}
            disabled={loading}
            className="whitespace-nowrap cursor-pointer text-xs font-mono font-bold text-red-500 hover:text-red-400 border border-red-500/30 hover:bg-red-500/10 px-4 py-2 rounded-lg transition-all"
        >
            {loading ? 'EXIT...' : 'LOGOUT'}
        </button>
    );
}

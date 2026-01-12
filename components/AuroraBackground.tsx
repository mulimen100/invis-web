"use client";
import React from "react";

interface AuroraBackgroundProps {
    variant?: "vibrant" | "muted";
}

export default function AuroraBackground({ variant = "vibrant" }: AuroraBackgroundProps) {
    const isMuted = variant === "muted";

    // Configuration Settings
    const opacityPrimary = isMuted ? "opacity-[0.08]" : "opacity-25";
    const opacitySecondary = isMuted ? "opacity-[0.06]" : "opacity-15";
    const opacityAccent = isMuted ? "opacity-[0.06]" : "opacity-15";

    const blurPrimary = isMuted ? "blur-[140px]" : "blur-[120px]";
    const blurSecondary = isMuted ? "blur-[120px]" : "blur-[100px]";
    const blurAccent = isMuted ? "blur-[100px]" : "blur-[80px]";

    return (
        <div className="fixed inset-0 z-0 bg-[#020617] overflow-hidden pointer-events-none">
            {/* 1. Top Center Glow (Primary Blurple) */}
            <div
                className={`absolute top-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-[#5865F2] rounded-full animate-blob ${opacityPrimary} ${blurPrimary} will-change-transform`}
            />

            {/* 2. Bottom Right (Deep Blue Depth) */}
            <div
                className={`absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-[#1E40AF] rounded-full animate-blob animation-delay-2000 ${opacitySecondary} ${blurSecondary} will-change-transform`}
            />

            {/* 3. Floating Accent (Soft Violet) */}
            <div
                className={`absolute top-[30%] left-[-10%] w-[400px] h-[400px] bg-[#A78BFA] rounded-full animate-blob animation-delay-4000 ${opacityAccent} ${blurAccent} will-change-transform`}
            />
        </div>
    );
}

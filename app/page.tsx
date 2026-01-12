export default function Home() {
  return (
    <div className="relative min-h-[calc(100vh-5rem)] flex flex-col items-center justify-center overflow-hidden">

      {/* Local Backgrounds removed to use Global Aura */}

      <div className="container mx-auto px-6 text-center z-10">
        <h1 className="text-6xl md:text-8xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
          INVIS
        </h1>
        <p className="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-12 font-light leading-relaxed">
          The next generation of autonomous trading intelligence.
          <br />
          <span className="text-blue-500 font-medium">Precision. Speed. Dominance.</span>
        </p>

        <div className="flex flex-col md:flex-row gap-6 justify-center">
          <a href="/arena" className="px-8 py-4 bg-white text-black font-semibold rounded-full hover:bg-gray-200 transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(255,255,255,0.3)]">
            Enter The Arena
          </a>
          <a href="/insights" className="px-8 py-4 bg-white/5 border border-white/10 text-white font-semibold rounded-full hover:bg-white/10 transition-all hover:scale-105 active:scale-95 backdrop-blur-md">
            View Insights
          </a>
        </div>
      </div>
    </div>
  );
}

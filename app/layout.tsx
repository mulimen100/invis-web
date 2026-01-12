import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import AuroraBackground from "../components/AuroraBackground";
import LogoutButton from "../components/LogoutButton";

export const metadata: Metadata = {
  title: "INVIS | Enterprise Intelligence",
  description: "Next-generation trading and intelligence systems.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#020617] text-gray-100 font-sans antialiased min-h-screen selection:bg-indigo-500 selection:text-white relative overflow-x-hidden">

        {/* Global Layer 1: Matte Gradient */}
        <div className="fixed inset-0 z-0 pointer-events-none aurora-bg animate-aurora" />

        {/* Global Layer 2: Floating Spheres */}
        <AuroraBackground variant="vibrant" />

        <div className="relative z-10 flex flex-col min-h-screen">
          {/* Navbar */}
          <header className="sticky top-0 z-50 border-b border-white/5 bg-[#020617]/50 backdrop-blur-xl">
            <div className="container mx-auto px-6 h-20 grid grid-cols-3 items-center">
              {/* Logo (Left) */}
              <div className="flex items-center justify-start">
                <Link href="/" className="text-3xl font-bold tracking-tighter text-white hover:opacity-80 transition-opacity">
                  INVIS
                </Link>
              </div>

              {/* Navigation (Center) */}
              <nav className="hidden md:flex items-center justify-center gap-10">
                <Link href="/" className="text-sm font-medium text-gray-300 hover:text-white hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all duration-300">
                  HOME
                </Link>
                <Link href="/insights" className="text-sm font-medium text-gray-300 hover:text-white hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all duration-300">
                  INSIGHTS
                </Link>
                <Link href="/arena" className="text-sm font-medium text-gray-300 hover:text-white hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all duration-300">
                  THE ARENA
                </Link>
                <Link href="/backtest" className="text-sm font-medium text-gray-300 hover:text-white hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all duration-300">
                  BACKTEST
                </Link>
              </nav>

              {/* Mobile Menu Placeholder */}
              <div className="flex justify-end md:hidden">
                <span className="text-gray-500 text-xs">[MENU]</span>
              </div>

              <div className="hidden md:flex justify-end">
                <LogoutButton />
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-grow">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t border-white/5 py-8 mt-auto bg-[#020617]/50 backdrop-blur-sm">
            <div className="container mx-auto px-6 text-center text-xs text-gray-500">
              &copy; {new Date().getFullYear()} INVIS SYSTEMS. ALL RIGHTS RESERVED.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

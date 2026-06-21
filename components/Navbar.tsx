'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Play, Trophy, Settings, Calculator, HelpCircle } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';

export function Navbar() {
  const pathname = usePathname();
  const { user, profile, logout } = useAuth();

  const navLinks = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/leaderboard', label: 'Leaderboard', icon: Trophy },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <nav className="border-b border-zinc-800/50 bg-zinc-950/50 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Calculator className="w-5 h-5 text-emerald-500" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">calculus.gg</span>
          </div>
          
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-zinc-800/50 text-emerald-500' 
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-800/30'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/help" className="text-zinc-400 hover:text-white transition-colors flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            <span className="text-sm font-medium hidden sm:inline">Help & Info</span>
          </Link>
          
          {user ? (
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-medium text-zinc-300">{profile?.displayName}</span>
              </div>
              <button
                onClick={logout}
                className="text-sm font-medium text-zinc-400 hover:text-white transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <Link
              href="/auth"
              className="px-5 py-2 bg-gradient-to-r from-emerald-400 to-cyan-400 text-black hover:from-emerald-300 hover:to-cyan-300 rounded-full text-sm font-bold transition-transform hover:scale-105 shadow-lg shadow-emerald-500/20"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

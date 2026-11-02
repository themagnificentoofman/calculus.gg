'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Home, Trophy, Settings, HelpCircle, Mail, Menu, X } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';

export function Navbar() {
  const pathname = usePathname();
  const { user, profile, logout, loading } = useAuth();
  const [open, setOpen] = useState(false);
  const links = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/leaderboard', label: 'Leaderboard', icon: Trophy },
    { href: '/settings', label: 'Settings', icon: Settings },
    { href: '/contact', label: 'Contact Us', icon: Mail },
  ];
  const navigation = links.map(({ href, label, icon: Icon }) => {
    const active = pathname === href;
    return <a key={href} href={href} aria-current={active ? 'page' : undefined} className={`min-h-11 flex items-center gap-2 rounded-xl px-3 text-sm font-medium ${active ? 'bg-zinc-800 text-emerald-400' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'}`}><Icon className="h-4 w-4 shrink-0" />{label}</a>;
  });
  return <nav aria-label="Main navigation" className="sticky top-0 z-30 border-b border-zinc-800/70 bg-zinc-950/95 backdrop-blur-xl">
    <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-2 px-3 sm:px-6 lg:px-8">
      <a href="/" aria-label="Calculus Ninja home" className="flex min-w-0 shrink-0 items-center gap-2 rounded-lg">
        <img src="/ninja-logo.png" alt="" width={40} height={40} className="h-10 w-10 shrink-0 object-contain" />
        <span className="text-base font-bold tracking-tight text-white sm:text-lg">Calculus Ninja</span>
      </a>
      <div className="hidden xl:flex items-center gap-1">{navigation}</div>
      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        <a aria-label="Help & Info" aria-current={pathname === '/help' ? 'page' : undefined} href="/help" className={`flex h-11 min-w-11 items-center justify-center gap-2 rounded-xl px-3 transition-colors ${pathname === '/help' ? 'bg-zinc-800 text-emerald-400' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'}`}><HelpCircle className="h-5 w-5 shrink-0" /><span className="hidden whitespace-nowrap text-sm lg:inline">Help & Info</span></a>
        {loading ? <span role="status" className="hidden sm:block text-xs text-zinc-400">Loading…</span> : user ? <>
          <span className="hidden lg:block max-w-32 truncate text-sm text-zinc-400">{profile?.displayName}</span>
          <button onClick={logout} className="hidden sm:block min-h-11 rounded-xl px-3 text-sm text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white">Sign Out</button>
        </> : <a href="/auth" className="hidden sm:flex min-h-11 items-center rounded-xl bg-emerald-400 px-4 text-sm font-bold text-zinc-950">Sign In</a>}
        <button aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)} className="flex h-11 w-11 items-center justify-center rounded-lg text-zinc-300 hover:bg-zinc-800 xl:hidden">{open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</button>
      </div>
    </div>
    {open && <div id="mobile-navigation" className="border-t border-zinc-800 p-3 xl:hidden"><div className="grid grid-cols-1 gap-1 sm:grid-cols-4">{navigation}</div>{!loading && <div className="mt-2 border-t border-zinc-800 pt-2 sm:hidden">{user ? <button onClick={logout} className="min-h-11 w-full rounded-xl px-3 text-left text-sm text-zinc-300">Sign Out</button> : <a href="/auth" className="flex min-h-11 items-center rounded-xl px-3 text-sm text-emerald-400">Sign In</a>}</div>}</div>}
  </nav>;
}

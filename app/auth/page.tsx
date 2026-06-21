'use client';

import { useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { Calculator, ArrowRight, Mail, Lock, User, Github } from 'lucide-react';
import Link from 'next/link';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, loginWithEmail, signupWithEmail } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        await loginWithEmail(email, password);
      } else {
        await signupWithEmail(email, password, name);
      }
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      await login();
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Google login failed');
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 dark:text-zinc-50 text-zinc-900 font-sans selection:bg-emerald-500/30">
      <Link href="/" className="absolute top-8 left-8 flex items-center gap-2 dark:text-zinc-400 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors">
        <Calculator className="w-6 h-6 text-emerald-500" />
        <span className="font-bold text-xl tracking-tight">CalcArena</span>
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl p-8 backdrop-blur-sm shadow-sm"
      >
        <h1 className="text-3xl font-bold mb-2 text-center">
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h1>
        <p className="dark:text-zinc-400 text-zinc-500 text-center mb-8">
          {isLogin ? 'Sign in to continue your grind.' : 'Join the ultimate calculus arena.'}
        </p>

        {error && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 text-red-500 dark:text-red-400 rounded-xl text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-500 mb-1">Display Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 dark:text-zinc-500 text-zinc-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full dark:bg-zinc-950 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-xl py-3 pl-10 pr-4 dark:text-white text-zinc-900 dark:placeholder-zinc-600 placeholder-zinc-400 focus:outline-none focus:border-emerald-500 transition-colors"
                  placeholder="Calculus Master"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-500 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 dark:text-zinc-500 text-zinc-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full dark:bg-zinc-950 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-xl py-3 pl-10 pr-4 dark:text-white text-zinc-900 dark:placeholder-zinc-600 placeholder-zinc-400 focus:outline-none focus:border-emerald-500 transition-colors"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-500 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 dark:text-zinc-500 text-zinc-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full dark:bg-zinc-950 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-xl py-3 pl-10 pr-4 dark:text-white text-zinc-900 dark:placeholder-zinc-600 placeholder-zinc-400 focus:outline-none focus:border-emerald-500 transition-colors"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
            {!loading && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t dark:border-zinc-800 border-zinc-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 dark:bg-zinc-900 bg-white dark:text-zinc-500 text-zinc-400">Or continue with</span>
          </div>
        </div>

        <button
          onClick={handleGoogleLogin}
          type="button"
          className="w-full py-3 dark:bg-zinc-800 bg-zinc-100 hover:bg-zinc-200 dark:hover:bg-zinc-700 dark:text-white text-zinc-900 font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Google
        </button>

        <p className="mt-8 text-center text-sm dark:text-zinc-400 text-zinc-500">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-emerald-500 hover:text-emerald-400 font-bold transition-colors"
          >
            {isLogin ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </motion.div>
    </main>
  );
}

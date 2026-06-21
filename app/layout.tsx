import type {Metadata} from 'next';
import './globals.css'; // Global styles
import 'katex/dist/katex.min.css'; // KaTeX styles
import { AuthProvider } from '@/components/AuthProvider';
import { ThemeProvider } from '@/components/ThemeProvider';
import { FriendsList } from '@/components/FriendsList';
import { Navbar } from '@/components/Navbar';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'what is bro doing on the calc',
  description: 'A competitive calculus trainer and multiplayer game with various modes, ratings, and step-by-step LaTeX explanations.',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="bg-background text-foreground min-h-screen font-sans antialiased hexagon-bg">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} forcedTheme="dark">
          <AuthProvider>
            <Navbar />
            {children}
            <FriendsList />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center">
      <h2 className="text-4xl font-bold mb-4">404 - Not Found</h2>
      <p className="text-xl text-zinc-400 mb-8">Could not find requested resource</p>
      <Link href="/" className="px-6 py-3 bg-white text-black rounded-full font-bold">
        Return Home
      </Link>
    </div>
  );
}

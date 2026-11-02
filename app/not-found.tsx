
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100dvh-4rem)] px-6 py-12 text-center">
      <h2 className="text-4xl font-bold mb-4">Page not found</h2>
      <p className="max-w-md text-lg leading-relaxed text-zinc-400 mb-8">This page is unavailable. Head home to continue practicing.</p>
      <a href="/" className="px-6 py-3 bg-white text-black rounded-full font-bold">
        Return Home
      </a>
    </div>
  );
}

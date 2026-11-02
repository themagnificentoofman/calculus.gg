'use client';
import { useEffect, useState } from 'react';
// Keep mobile utility panels from covering one another.
export function usePanel(name: string): [boolean, (open: boolean) => void] {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const panel = (event: Event) => { if ((event as CustomEvent).detail !== name) setOpen(false); };
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false); };
    window.addEventListener('calculus-panel', panel); window.addEventListener('keydown', key);
    return () => { window.removeEventListener('calculus-panel', panel); window.removeEventListener('keydown', key); };
  }, [name]);
  return [open, value => { if (value) window.dispatchEvent(new CustomEvent('calculus-panel', { detail: name })); setOpen(value); }];
}

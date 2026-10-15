"use client";

import { useEffect } from "react";
import { imageSrc } from "@/lib/api";

export type Slide = { label: string; image_url: string | null; section?: string | null };

/** Overlay with one page image; closes on Esc, the backdrop or the button. */
export default function SlideModal({ slide, onClose }: { slide: Slide | null; onClose: () => void }) {
  useEffect(() => {
    if (!slide) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [slide, onClose]);

  if (!slide) return null;
  const src = imageSrc(slide.image_url);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="max-h-full w-full max-w-4xl overflow-auto rounded-lg bg-white p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label={slide.label}
      >
        <div className="mb-3 flex items-start justify-between gap-4">
          <div>
            <p className="font-semibold">{slide.label}</p>
            {slide.section && <p className="text-sm text-slate-500">{slide.section}</p>}
          </div>
          <button onClick={onClose} className="rounded border px-2 py-1 text-sm hover:bg-slate-100">
            Close
          </button>
        </div>
        {src ? (
          // a plain <img>: the PNG comes from the local API, next/image optimisation adds nothing here
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={slide.label} className="w-full rounded border" />
        ) : (
          <p className="text-slate-500">No image for this page.</p>
        )}
      </div>
    </div>
  );
}

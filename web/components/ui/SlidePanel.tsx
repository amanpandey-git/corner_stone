"use client";

import { ChevronLeft, ChevronRight, ExternalLink, X } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { imageSrc } from "@/lib/api";
import { splitLabel } from "@/lib/format";
import { Button } from "./Button";

export type Slide = { label: string; image_url: string | null; section?: string | null; text?: string | null; n?: number };

type Props = { slides: Slide[]; index: number; onIndex: (i: number) => void; onClose: () => void };

/** The slide itself. Slides are 1100 x 619, so the frame is reserved and nothing jumps while the image loads. */
export function SlideImage({ slide, className, sizes }: { slide: Slide; className?: string; sizes?: string }) {
  const src = imageSrc(slide.image_url);
  const [failed, setFailed] = useState<string | null>(null);
  const alt = `Slide: ${slide.label}${slide.section ? `, ${slide.section}` : ""}`;
  return (
    <div className={`aspect-[1100/619] overflow-hidden rounded-md border bg-sunk ${className ?? ""}`}>
      {src && failed !== src ? (
        // a plain <img>: the WebP files are already sized for this frame, next/image optimisation adds nothing
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={src}
          src={src}
          alt={alt}
          width={1100}
          height={619}
          sizes={sizes}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(src)}
          className="slide-img h-full w-full object-contain"
        />
      ) : (
        <p className="flex h-full items-center justify-center p-4 text-small text-ink-3">No image for this page.</p>
      )}
    </div>
  );
}

function Body({ slides, index, onIndex, onClose, headingRef }: Props & { headingRef?: React.Ref<HTMLHeadingElement> }) {
  const slide = slides[index];
  const { deck, page } = splitLabel(slide.label);
  return (
    <div className="space-y-4 p-4 md:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 ref={headingRef} tabIndex={-1} className="font-sans text-h3 focus:outline-none" title={slide.label}>
            {slide.section ?? deck}
          </h2>
          <p className="text-small text-ink-2">{deck}{page && <span className="font-mono text-mono"> · {page}</span>}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close slide"
          className="-mr-2 -mt-2 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-sm text-ink-2 hover:bg-sunk hover:text-ink"
        >
          <X size={20} strokeWidth={1.5} aria-hidden />
        </button>
      </div>
      <SlideImage slide={slide} />
      {/* What the slide says, for screen readers: the same text the answer was written from. */}
      {slide.text && <p className="sr-only">{slide.text}</p>}
      <div className="flex flex-wrap items-center justify-between gap-2">
        {slides.length > 1 ? (
          <div className="flex items-center gap-1">
            <Button variant="secondary" size="sm" disabled={index === 0} onClick={() => onIndex(index - 1)} aria-label="Previous slide">
              <ChevronLeft size={16} strokeWidth={1.5} aria-hidden />
            </Button>
            <span className="px-1 font-mono text-mono text-ink-2" aria-live="polite">{index + 1} of {slides.length}</span>
            <Button variant="secondary" size="sm" disabled={index === slides.length - 1} onClick={() => onIndex(index + 1)} aria-label="Next slide">
              <ChevronRight size={16} strokeWidth={1.5} aria-hidden />
            </Button>
          </div>
        ) : <span />}
        {imageSrc(slide.image_url) && (
          <a href={imageSrc(slide.image_url) ?? undefined} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center gap-1.5 rounded-sm px-2 text-small text-accent-ink underline-offset-4 hover:underline">
            Open full size
            <ExternalLink size={14} strokeWidth={1.5} aria-hidden />
          </a>
        )}
      </div>
    </div>
  );
}

/**
 * Beside the answer on wide screens, so the claim and its slide can be read together. `takeFocus` is true when the
 * student opened it; a panel that opens by itself after an answer leaves focus in the question box.
 */
export function SlideDock({ takeFocus, ...props }: Props & { takeFocus?: boolean }) {
  const { onClose } = props;
  const heading = useRef<HTMLHeadingElement>(null);
  const closer = useRef(onClose);
  useEffect(() => {
    closer.current = onClose;
  }, [onClose]);
  const [wanted] = useState(takeFocus);
  useEffect(() => {
    // Keep where focus was, move it into the panel, and give it back on close.
    const opener = wanted ? (document.activeElement as HTMLElement | null) : null;
    if (wanted) heading.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closer.current();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      if (opener?.isConnected) opener.focus();
    };
  }, [wanted]);
  return (
    <aside aria-label="Source slide" className="panel-in rounded-xl border bg-raised shadow-sheet">
      <Body {...props} headingRef={heading} />
    </aside>
  );
}

/** A native <dialog>: focus trap, Esc and focus return come from the browser. Bottom sheet on phones, side drawer on desktop. */
export function SlideDialog(props: Props) {
  const { onClose } = props;
  const ref = useRef<HTMLDialogElement>(null);
  useLayoutEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
    return () => {
      if (d?.open) d.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-label="Source slide"
      className="slide-dialog"
      onCancel={(e) => { e.preventDefault(); onClose(); }}
      onClick={(e) => { if (e.target === ref.current) onClose(); }}
    >
      <Body {...props} />
    </dialog>
  );
}

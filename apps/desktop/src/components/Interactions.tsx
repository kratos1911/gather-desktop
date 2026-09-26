import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import Lenis from "lenis";
import { ThinkingOrb } from "thinking-orbs";

// Original implementation inspired by Motion Primitives' shared-layout background.
// This is controlled by the selected filter, not pointer hover.
export function FilterControl({
  items,
  value,
  onChange,
}: {
  items: string[];
  value: string;
  onChange: (value: string) => void;
}) {
  const id = useId();
  const reduced = useReducedMotion();
  return (
    <div className="filters" role="group" aria-label="File type">
      {items.map((item) => (
        <button
          key={item}
          aria-pressed={value === item}
          className="filter"
          onClick={() => onChange(item)}
        >
          {value === item && (
            <motion.span
              className="filter-background"
              layoutId={reduced ? undefined : id}
              transition={{ duration: reduced ? 0 : 0.18 }}
            />
          )}
          <span className="filter-label">{item}</span>
        </button>
      ))}
    </div>
  );
}

export function ReadingPane({ children }: { children: ReactNode }) {
  const wrapper = useRef<HTMLDivElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const [smooth, setSmooth] = useState(false);
  useEffect(() => {
    if (!smooth || reduced || !wrapper.current || !content.current) return;
    const lenis = new Lenis({
      wrapper: wrapper.current,
      content: content.current,
      autoRaf: true,
      duration: 0.65,
      smoothWheel: true,
      syncTouch: false,
    });
    return () => lenis.destroy();
  }, [smooth, reduced]);
  return (
    <div className="reading-wrapper">
      <label className="reading-option">
        <input
          type="checkbox"
          checked={smooth}
          disabled={!!reduced}
          onChange={(e) => setSmooth(e.target.checked)}
        />{" "}
        Smooth reading scroll{reduced ? " (disabled by reduced motion)" : ""}
      </label>
      <div ref={wrapper} className="reader-scroll">
        <div ref={content} className="reader">
          {children}
        </div>
      </div>
    </div>
  );
}

export function OrbPreview() {
  const [play, setPlay] = useState(false);
  return (
    <section className="orb-preview" aria-label="Processing indicator preview">
      <ThinkingOrb
        state="searching"
        size={20}
        theme="light"
        paused={!play}
        aria-label="Sample processing indicator, not an active job"
      />
      <p>Processing indicator sample. No model is running.</p>
      <button className="back" onClick={() => setPlay(!play)}>
        {play ? "Pause sample" : "Preview motion"}
      </button>
    </section>
  );
}

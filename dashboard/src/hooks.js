import { useEffect, useRef, useState } from "react";

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Dark/light theme persisted to localStorage, applied to <html data-theme>. */
export function useTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof localStorage !== "undefined" && localStorage.getItem("theme")) {
      return localStorage.getItem("theme");
    }
    return "dark";
  });
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

/** Count up to `target` once `run` is true (instant if reduced-motion). */
export function useCountUp(target, run, ms = 900) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!run) return;
    if (prefersReducedMotion()) {
      setN(target);
      return;
    }
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - t, 3);
      setN(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, run, ms]);
  return n;
}

/** True once the ref scrolls into view (immediately if reduced-motion).
 * Uses threshold 0 + a bottom rootMargin so it fires when the element ENTERS the
 * viewport, not when 15% of it is visible — a fixed 15% ratio never triggers on
 * sections taller than ~6x the viewport (e.g. the full 52-card projects grid),
 * which leaves the whole section stuck at opacity:0. */
export function useInView(options = { threshold: 0, rootMargin: "0px 0px -10% 0px" }) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (prefersReducedMotion()) {
      setInView(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        setInView(true);
        obs.disconnect();
      }
    }, options);
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, inView];
}

/** Lock body scroll while a modal is open. */
export function useBodyLock(active) {
  useEffect(() => {
    if (!active) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [active]);
}

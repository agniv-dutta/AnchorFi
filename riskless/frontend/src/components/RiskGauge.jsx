import { useEffect, useMemo, useState } from "react";

function colorFor(score) {
  if (score >= 70) return { stroke: "stroke-rose-500", text: "text-rose-200" };
  if (score >= 40) return { stroke: "stroke-amber-400", text: "text-amber-100" };
  return { stroke: "stroke-emerald-400", text: "text-emerald-100" };
}

export default function RiskGauge({ score }) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    setAnimated(0);
    const start = performance.now();
    const dur = 1500;
    let raf = 0;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      setAnimated(Math.round(score * p));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const r = 54;
  const c = 2 * Math.PI * r;
  const dash = (animated / 100) * c;
  const theme = useMemo(() => colorFor(score), [score]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
      <div className="text-xs uppercase tracking-widest text-slate-400">
        Composite risk score
      </div>
      <div className="mt-4 flex items-center justify-center">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r={r}
            fill="none"
            strokeWidth="12"
            className="stroke-slate-800"
          />
          <circle
            cx="80"
            cy="80"
            r={r}
            fill="none"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c - dash}`}
            transform="rotate(-90 80 80)"
            className={theme.stroke}
          />
          <text
            x="80"
            y="86"
            textAnchor="middle"
            className={`fill-current text-3xl font-semibold ${theme.text}`}
          >
            {animated}
          </text>
        </svg>
      </div>
      <div className="mt-2 text-center text-xs text-slate-400">
        0 = lowest risk, 100 = highest risk
      </div>
    </div>
  );
}


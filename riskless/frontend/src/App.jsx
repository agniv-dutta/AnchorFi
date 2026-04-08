import { useMemo, useState } from "react";
import AddressInput from "./components/AddressInput.jsx";
import RiskGauge from "./components/RiskGauge.jsx";
import RiskBreakdown from "./components/RiskBreakdown.jsx";
import PremiumEstimate from "./components/PremiumEstimate.jsx";
import AssessmentHistory from "./components/AssessmentHistory.jsx";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function formatUsdc(x) {
  if (typeof x !== "number" || Number.isNaN(x)) return "—";
  return x.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export default function App() {
  const [target, setTarget] = useState("");
  const [coverageAmount, setCoverageAmount] = useState(10000);
  const [coverageDays, setCoverageDays] = useState(30);
  const [loadingStep, setLoadingStep] = useState(null); // 0..2
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const loadingLabel = useMemo(() => {
    if (loadingStep === 0) return "Fetching on-chain data…";
    if (loadingStep === 1) return "Running AI analysis…";
    if (loadingStep === 2) return "Calculating premium…";
    return "";
  }, [loadingStep]);

  async function runAssess() {
    setError("");
    setResult(null);
    setLoadingStep(0);
    const t0 = window.setTimeout(() => setLoadingStep(1), 2500);
    const t1 = window.setTimeout(() => setLoadingStep(2), 5200);
    try {
      const resp = await fetch(`${API_BASE}/assess`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          target,
          coverage_amount: Number(coverageAmount),
          coverage_days: Number(coverageDays),
        }),
      });
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setResult(data);
      document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      setError(e?.message || "Request failed");
    } finally {
      window.clearTimeout(t0);
      window.clearTimeout(t1);
      setLoadingStep(null);
    }
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <header className="flex items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-widest text-slate-400">
              AnchorFi
            </div>
            <h1 className="text-3xl font-semibold">RiskLens</h1>
          </div>
          <div className="rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
            Ethereum mainnet only (v1)
          </div>
        </header>

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
          <div className="grid gap-6 md:grid-cols-12 md:items-end">
            <div className="md:col-span-7">
              <h2 className="text-2xl font-semibold">
                Instant DeFi insurance risk assessment
              </h2>
              <p className="mt-2 text-sm text-slate-300">
                Paste a contract address or DeFi protocol name to get a risk score,
                plain-English breakdown, and a dynamic premium estimate in under 10
                seconds.
              </p>
            </div>
            <div className="md:col-span-5">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-slate-400">Coverage</label>
                  <input
                    value={coverageAmount}
                    onChange={(e) => setCoverageAmount(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
                    inputMode="numeric"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Days</label>
                  <input
                    value={coverageDays}
                    onChange={(e) => setCoverageDays(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
                    inputMode="numeric"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={runAssess}
                    disabled={!target.trim() || loadingStep !== null}
                    className="w-full rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Assess Risk
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <AddressInput value={target} onChange={setTarget} />
            {error ? (
              <div className="mt-3 rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-sm text-rose-200">
                {error}
              </div>
            ) : null}
            {loadingStep !== null ? (
              <div className="mt-4 flex items-center gap-3 text-sm text-slate-300">
                <div className="h-2 w-2 animate-pulse rounded-full bg-indigo-400" />
                <div>{loadingLabel}</div>
              </div>
            ) : null}
          </div>
        </section>

        <section id="results" className="mt-10">
          {result ? (
            <div className="grid gap-6 lg:grid-cols-12">
              <div className="lg:col-span-4">
                <RiskGauge score={result.composite_risk_score} />
                <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                  <div className="text-xs uppercase tracking-widest text-slate-400">
                    Estimated premium
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {formatUsdc(result.premium_usdc)} USDC
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    Illustrative only. Not an actual policy quote.
                  </div>
                </div>
              </div>
              <div className="lg:col-span-8">
                <RiskBreakdown result={result} />
                <PremiumEstimate
                  coverageAmount={coverageAmount}
                  coverageDays={coverageDays}
                  premium={result.premium_usdc}
                />
                {result.ai ? (
                  <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="text-sm font-semibold">AI underwriter note</div>
                      <span className="rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-xs text-slate-200">
                        {result.ai.recommended_action}
                      </span>
                    </div>
                    <blockquote className="mt-4 border-l-2 border-indigo-500/60 pl-4 text-sm text-slate-200">
                      {result.ai.summary}
                    </blockquote>
                    <div className="mt-4 text-xs text-slate-400">
                      Confidence: {result.ai.confidence}
                    </div>
                    <div className="mt-3">
                      <div className="text-xs uppercase tracking-widest text-slate-400">
                        Top risks
                      </div>
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-200">
                        {result.ai.top_risks?.slice(0, 3).map((x) => (
                          <li key={x}>{x}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/40 p-6 text-sm text-slate-300">
                    AI narrative is disabled (set `GROQ_API_KEY` or `ANTHROPIC_API_KEY`).
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-900 bg-slate-950/20 p-10 text-center text-sm text-slate-400">
              Results will appear here after assessment.
            </div>
          )}
        </section>

        <section className="mt-10">
          <AssessmentHistory apiBase={API_BASE} />
        </section>

        <footer className="mt-12 text-xs text-slate-500">
          AnchorFi RiskLens is a hackathon demo. No funds, policies, or guarantees.
        </footer>
      </div>
    </div>
  );
}


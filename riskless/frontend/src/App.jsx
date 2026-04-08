import { useEffect, useMemo, useState } from "react";
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

function toOptionalNumber(value) {
  if (value === "" || value === null || value === undefined) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

function reportUrl(reportUuid) {
  return `${API_BASE}/report/${reportUuid}`;
}

function getNearMissCount(result) {
  return result?.raw_signals?.defi?.protocol?.near_misses?.length ?? 0;
}

function CompareCard({ item, winner }) {
  const nearMissCount = getNearMissCount(item);
  return (
    <div
      className={`rounded-2xl border p-5 ${
        winner
          ? "border-emerald-500/70 bg-emerald-950/20"
          : "border-slate-800 bg-slate-950/40"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-widest text-slate-400">Target</div>
          <div className="mt-1 text-xl font-semibold">{item.target}</div>
        </div>
        {winner ? (
          <span className="rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-200">
            Winner
          </span>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs uppercase tracking-widest text-slate-500">Score</div>
          <div className="mt-1 text-2xl font-semibold">{item.composite_risk_score}/100</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs uppercase tracking-widest text-slate-500">Premium</div>
          <div className="mt-1 text-2xl font-semibold">
            {formatUsdc(item.premium_usdc)} USDC
          </div>
        </div>
      </div>

      {nearMissCount > 0 ? (
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">
          {nearMissCount} similar protocols were exploited in the past 2 years.
        </div>
      ) : null}

      {item.ai ? (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-slate-200">
          <div className="font-semibold">{item.ai.recommended_action}</div>
          <div className="mt-2 text-slate-300">{item.ai.summary}</div>
          <div className="mt-3 text-xs text-slate-400">
            Confidence: {item.ai.confidence}
            {item.ai.recommended_coverage_percentage != null ? (
              <span>
                {' '}
                · Recommended coverage: {item.ai.recommended_coverage_percentage}%
                {item.ai.recommended_coverage_amount != null
                  ? ` (${formatUsdc(item.ai.recommended_coverage_amount)} USDC)`
                  : ""}
              </span>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3">
        <a
          href={reportUrl(item.report_uuid)}
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-2 text-sm text-slate-200"
        >
          Open report
        </a>
      </div>
    </div>
  );
}

export default function App() {
  const [target, setTarget] = useState("");
  const [compareTargets, setCompareTargets] = useState(["AAVE", "Compound", "Uniswap"]);
  const [coverageAmount, setCoverageAmount] = useState(10000);
  const [coverageDays, setCoverageDays] = useState(30);
  const [walletValue, setWalletValue] = useState("");
  const [loadingStep, setLoadingStep] = useState(null); // 0..2
  const [compareLoading, setCompareLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [watchlistAddress, setWatchlistAddress] = useState("");
  const [watchlistItems, setWatchlistItems] = useState([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [watchlistError, setWatchlistError] = useState("");

  const loadingLabel = useMemo(() => {
    if (loadingStep === 0) return "Fetching on-chain data…";
    if (loadingStep === 1) return "Running AI analysis…";
    if (loadingStep === 2) return "Calculating premium…";
    return "";
  }, [loadingStep]);

  const walletValueNumber = useMemo(() => toOptionalNumber(walletValue), [walletValue]);

  async function refreshWatchlist() {
    setWatchlistError("");
    setWatchlistLoading(true);
    try {
      const r = await fetch(`${API_BASE}/watchlist`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setWatchlistItems(data.items || []);
    } catch (e) {
      setWatchlistError(e?.message || "Failed to load watchlist");
    } finally {
      setWatchlistLoading(false);
    }
  }

  useEffect(() => {
    void refreshWatchlist();
  }, []);

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
          wallet_value: walletValueNumber,
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

  async function runCompare() {
    setCompareError("");
    setCompareResult(null);
    const normalizedTargets = compareTargets.map((value) => value.trim()).filter(Boolean);
    if (normalizedTargets.length < 2) {
      setCompareError("Enter at least two targets to compare.");
      return;
    }
    setCompareLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          targets: normalizedTargets,
          coverage_amount: Number(coverageAmount),
          coverage_days: Number(coverageDays),
          wallet_value: walletValueNumber,
        }),
      });
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setCompareResult(data);
      document.getElementById("compare-results")?.scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      setCompareError(e?.message || "Compare request failed");
    } finally {
      setCompareLoading(false);
    }
  }

  async function addWatchlistAddress() {
    setWatchlistError("");
    if (!watchlistAddress.trim()) return;
    try {
      const resp = await fetch(`${API_BASE}/watchlist/${encodeURIComponent(watchlistAddress.trim())}`, {
        method: "POST",
      });
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `HTTP ${resp.status}`);
      }
      setWatchlistAddress("");
      await refreshWatchlist();
    } catch (e) {
      setWatchlistError(e?.message || "Failed to add address");
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
            <h1 className="text-3xl font-semibold">AnchorFi</h1>
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
                <div>
                  <label className="text-xs text-slate-400">Wallet value</label>
                  <input
                    value={walletValue}
                    onChange={(e) => setWalletValue(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
                    inputMode="decimal"
                    placeholder="Optional"
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

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-widest text-slate-400">Comparison</div>
              <h2 className="mt-1 text-2xl font-semibold">Compare up to 3 protocols</h2>
            </div>
            <button
              onClick={runCompare}
              disabled={compareLoading}
              className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-2 text-sm font-medium text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {compareLoading ? "Comparing…" : "Compare targets"}
            </button>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {compareTargets.map((value, index) => (
              <div key={index}>
                <label className="text-xs text-slate-400">Target {index + 1}</label>
                <input
                  value={value}
                  onChange={(e) => {
                    const next = [...compareTargets];
                    next[index] = e.target.value;
                    setCompareTargets(next);
                  }}
                  placeholder={index === 0 ? "AAVE" : index === 1 ? "Compound" : "Uniswap"}
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
                />
              </div>
            ))}
          </div>

          {compareError ? (
            <div className="mt-4 rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-sm text-rose-200">
              {compareError}
            </div>
          ) : null}
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
                <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-sm text-slate-200">
                  <div className="text-xs uppercase tracking-widest text-slate-400">
                    Shareable report
                  </div>
                  <a
                    href={reportUrl(result.report_uuid)}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm font-medium text-slate-100"
                  >
                    Open report page
                  </a>
                </div>
              </div>
              <div className="lg:col-span-8">
                <RiskBreakdown result={result} />
                <PremiumEstimate
                  coverageAmount={coverageAmount}
                  coverageDays={coverageDays}
                  premium={result.premium_usdc}
                />
                {getNearMissCount(result) > 0 ? (
                  <div className="mt-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6 text-sm text-amber-100">
                    {getNearMissCount(result)} similar protocols were exploited in the past 2 years.
                  </div>
                ) : null}
                {result.ai?.recommended_coverage_percentage != null ? (
                  <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/40 p-6 text-sm text-slate-200">
                    <div className="text-xs uppercase tracking-widest text-slate-400">
                      Coverage recommendation
                    </div>
                    <div className="mt-2 text-lg font-semibold">
                      Insure {result.ai.recommended_coverage_percentage}% of wallet value
                    </div>
                    <div className="mt-1 text-slate-300">
                      {result.ai.recommended_coverage_amount != null
                        ? `${formatUsdc(result.ai.recommended_coverage_amount)} USDC recommended`
                        : "Provide wallet value to estimate a coverage amount."}
                    </div>
                  </div>
                ) : null}
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

        <section id="compare-results" className="mt-10">
          {compareResult?.items?.length ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-widest text-slate-400">Comparison results</div>
                  <h2 className="mt-1 text-2xl font-semibold">Side-by-side protocol review</h2>
                </div>
                {compareResult.winner_target ? (
                  <div className="rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1 text-xs text-emerald-100">
                    Winner: {compareResult.winner_target}
                  </div>
                ) : null}
              </div>
              <div className="mt-6 grid gap-4 lg:grid-cols-3">
                {compareResult.items.map((item) => (
                  <CompareCard
                    key={item.report_uuid}
                    item={item}
                    winner={item.report_uuid === compareResult.winner_report_uuid}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </section>

        <section className="mt-10">
          <AssessmentHistory apiBase={API_BASE} />
        </section>

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-widest text-slate-400">Watchlist</div>
              <h2 className="mt-1 text-2xl font-semibold">Monitor contract addresses</h2>
            </div>
            <button
              onClick={refreshWatchlist}
              className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-2 text-sm font-medium text-slate-100"
            >
              Refresh watchlist
            </button>
          </div>

          <div className="mt-5 flex flex-col gap-3 md:flex-row">
            <input
              value={watchlistAddress}
              onChange={(e) => setWatchlistAddress(e.target.value)}
              placeholder="0x..."
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-slate-600"
            />
            <button
              onClick={addWatchlistAddress}
              className="rounded-lg bg-indigo-500 px-4 py-3 text-sm font-medium text-white"
            >
              Add to watchlist
            </button>
          </div>

          {watchlistError ? (
            <div className="mt-4 rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-sm text-rose-200">
              {watchlistError}
            </div>
          ) : null}

          <div className="mt-5 space-y-3">
            {watchlistLoading ? (
              <div className="text-sm text-slate-400">Refreshing watchlist…</div>
            ) : null}
            {!watchlistLoading && watchlistItems.length === 0 ? (
              <div className="text-sm text-slate-400">No watchlist items yet.</div>
            ) : null}
            {watchlistItems.map((item) => (
              <div
                key={item.address}
                className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="font-mono text-sm text-slate-100">{item.address}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    Previous score: {item.previous_score ?? "—"} · Current score: {item.current_score ?? "—"}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {item.risk_increased ? (
                    <span className="rounded-full border border-rose-500/40 bg-rose-500/15 px-3 py-1 text-xs text-rose-100">
                      Risk increased
                    </span>
                  ) : (
                    <span className="rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1 text-xs text-emerald-100">
                      Stable
                    </span>
                  )}
                  <a
                    href={reportUrl(item.report_uuid)}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-100"
                  >
                    Report
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        <footer className="mt-12 text-xs text-slate-500">
          AnchorFi is a hackathon demo. No funds, policies, or guarantees.
        </footer>
      </div>
    </div>
  );
}


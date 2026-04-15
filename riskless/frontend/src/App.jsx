import { useEffect, useMemo, useState } from "react";

import "./App.css";
import AssessForm from "./components/AssessForm";
import ComparePanel from "./components/ComparePanel";
import EmptyState from "./components/EmptyState";
import LoadingState from "./components/LoadingState";
import Nav from "./components/Nav";
import RecentTable from "./components/RecentTable";
import ResultsPanel from "./components/ResultsPanel";
import Ticker from "./components/Ticker";
import WatchList from "./components/WatchList";

const API = "/api";

export default function App() {
  const [assessResult, setAssessResult] = useState(null);
  const [compareResults, setCompareResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [currentTarget, setCurrentTarget] = useState("");
  const [coverageAmount, setCoverageAmount] = useState(10000);
  const [coverageDays, setCoverageDays] = useState(30);
  const [compare, setCompare] = useState({ p1: "aave", p2: "compound", p3: "" });
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState(null);
  const [watchAddress, setWatchAddress] = useState("");
  const [animatedScore, setAnimatedScore] = useState(0);

  async function fetchHistory() {
    const resp = await fetch(`${API}/history`);
    const data = await resp.json();
    setHistory(data.items || []);
  }

  async function fetchWatchlist() {
    const resp = await fetch(`${API}/watchlist`);
    const data = await resp.json();
    setWatchlist(data.items || []);
  }

  useEffect(() => {
    fetchHistory().catch(() => {});
    fetchWatchlist().catch(() => {});
  }, []);

  useEffect(() => {
    if (!assessResult) return;
    setAnimatedScore(0);
    const target = assessResult.composite_risk_score;
    const step = Math.max(1, Math.ceil(target / 40));
    const id = window.setInterval(() => {
      setAnimatedScore((v) => {
        const next = Math.min(target, v + step);
        if (next >= target) window.clearInterval(id);
        return next;
      });
    }, 20);
    return () => window.clearInterval(id);
  }, [assessResult]);

  const timelineHistory = useMemo(() => {
    if (!assessResult) return [];
    return history.filter((item) => String(item.target).toLowerCase() === String(assessResult.target).toLowerCase());
  }, [history, assessResult]);

  async function handleAssess(targetOverride) {
    try {
      const target = (targetOverride ?? currentTarget).trim();
      if (!target) return;
      setLoading(true);
      setError(null);
      setAssessResult(null);
      setLoadingStep(0);
      window.setTimeout(() => setLoadingStep(1), 700);
      window.setTimeout(() => setLoadingStep(2), 1400);
      window.setTimeout(() => setLoadingStep(3), 1800);

      const resp = await fetch(`${API}/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, coverage_amount: coverageAmount, coverage_days: coverageDays }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) throw new Error(data.error || `HTTP ${resp.status}`);
      setCurrentTarget(target);
      setAssessResult(data);
      await fetchHistory();
    } catch (err) {
      setError(err?.message || "Unknown request failure");
    } finally {
      setLoading(false);
    }
  }

  async function handleCompare() {
    try {
      setCompareLoading(true);
      setCompareError(null);
      const targets = [compare.p1, compare.p2, compare.p3].filter(Boolean);
      const resp = await fetch(`${API}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ targets, coverage_amount: coverageAmount, coverage_days: coverageDays }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) throw new Error(data.error || `HTTP ${resp.status}`);
      setCompareResults(data.results || []);
    } catch (err) {
      setCompareError(err?.message || "Compare failed");
    } finally {
      setCompareLoading(false);
    }
  }

  async function handleWatchlistAdd() {
    try {
      if (!watchAddress.trim()) return;
      const resp = await fetch(`${API}/watchlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: watchAddress.trim() }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) throw new Error(data.error || `HTTP ${resp.status}`);
      setWatchAddress("");
      await fetchWatchlist();
    } catch (err) {
      setError(err?.message || "Watchlist add failed");
    }
  }

  async function handleWatchlistRefresh() {
    try {
      const resp = await fetch(`${API}/watchlist/refresh`);
      const data = await resp.json();
      if (!resp.ok || data.error) throw new Error(data.error || `HTTP ${resp.status}`);
      setWatchlist(data.items || []);
    } catch (err) {
      setError(err?.message || "Watchlist refresh failed");
    }
  }

  async function handleWatchlistRemove(address) {
    await fetch(`${API}/watchlist/${encodeURIComponent(address)}`, { method: "DELETE" });
    await fetchWatchlist();
  }

  return (
    <div className="app-wrap">
      <Nav />
      <Ticker />
      <main className="main-shell">
        <AssessForm
          currentTarget={currentTarget}
          setCurrentTarget={setCurrentTarget}
          coverageAmount={coverageAmount}
          setCoverageAmount={setCoverageAmount}
          coverageDays={coverageDays}
          setCoverageDays={setCoverageDays}
          onAssess={() => handleAssess()}
          onDemo={(target) => {
            setCurrentTarget(target);
            handleAssess(target);
          }}
        />

        {error ? (
          <div className="error-box">
            <div style={{ fontWeight: 900, marginBottom: 8 }}>ASSESSMENT FAILED</div>
            <div>{error}</div>
            <div style={{ marginTop: 8, color: "#888", fontSize: 10 }}>CHECK: BACKEND ON PORT 8000? VITE PROXY SET?</div>
          </div>
        ) : null}

        {loading ? <LoadingState step={loadingStep} /> : null}
        {!loading && !assessResult && !error ? <EmptyState /> : null}
        {assessResult ? (
          <ResultsPanel
            assessResult={assessResult}
            animatedScore={animatedScore}
            history={timelineHistory}
          />
        ) : null}

        <ComparePanel
          compare={compare}
          setCompare={setCompare}
          onCompare={handleCompare}
          compareResults={compareResults}
          compareLoading={compareLoading}
          compareError={compareError}
        />
        <WatchList
          watchAddress={watchAddress}
          setWatchAddress={setWatchAddress}
          watchlist={watchlist}
          onAdd={handleWatchlistAdd}
          onRefresh={handleWatchlistRefresh}
          onRemove={handleWatchlistRemove}
        />
        <RecentTable history={history} onPick={(target) => handleAssess(target)} />

        <footer className="footer">
          <div>ANCHORFI V0.1.0 — HASHKEY CHAIN HORIZON HACKATHON 2026</div>
          <div>ANCHORFI IS A DEMO. NO FUNDS, POLICIES, OR GUARANTEES.</div>
        </footer>
      </main>
    </div>
  );
}

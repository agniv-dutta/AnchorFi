import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function formatUsdc(x) {
  if (typeof x !== "number" || Number.isNaN(x)) return "—";
  return x.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function toOptionalNumber(value) {
  if (value === "" || value === null || value === undefined) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

function animateScore(target, el) {
  let current = 0;
  el.textContent = "0";
  const step = Math.max(1, Math.ceil(target / 40));
  const interval = window.setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = String(current);
    if (current >= target) {
      window.clearInterval(interval);
    }
  }, 20);
  return () => window.clearInterval(interval);
}

function formatHistoryDate(item) {
  const raw = item?.timestamp ?? item?.created_at ?? item?.as_of;
  if (raw === null || raw === undefined || raw === "") return "—";
  const d = new Date(typeof raw === "number" ? raw * 1000 : raw);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
}

export default function App() {
  const [target, setTarget] = useState("");
  const [coverageAmount, setCoverageAmount] = useState(10000);
  const [coverageDays, setCoverageDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0); // 0, 1, 2, 3 (finished)
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [barsArmed, setBarsArmed] = useState(false);
  const scoreRef = useRef(null);

  const [compareTargets, setCompareTargets] = useState(["AAVE", "COMPOUND", "UNISWAP"]);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [compareError, setCompareError] = useState("");

  const [watchlistAddress, setWatchlistAddress] = useState("");
  const [watchlistItems, setWatchlistItems] = useState([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [watchlistError, setWatchlistError] = useState("");

  async function fetchHistory() {
    try {
      const r = await fetch(`${API_BASE}/history`);
      if (r.ok) {
        const data = await r.json();
        setHistory(data.items || []);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  }

  useEffect(() => {
    fetchHistory();
  }, []);

  async function fetchWatchlist() {
    setWatchlistLoading(true);
    try {
      const r = await fetch(`${API_BASE}/watchlist`);
      if (r.ok) {
        const data = await r.json();
        setWatchlistItems(data.items || []);
      }
    } catch (e) {
      console.error("Failed to fetch watchlist", e);
    } finally {
      setWatchlistLoading(false);
    }
  }

  useEffect(() => {
    void fetchWatchlist();
  }, []);

  async function runCompare() {
    setCompareError("");
    setCompareResult(null);
    const targets = compareTargets.map(t => t.trim()).filter(Boolean);
    if (targets.length < 2) {
      setCompareError("Please enter at least 2 targets to compare.");
      return;
    }
    setCompareLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          targets: targets,
          coverage_amount: Number(coverageAmount),
          coverage_days: Number(coverageDays),
        }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
      }
      setCompareResult(data);
      document.getElementById("compare-results")?.scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      setCompareError(e?.message || "Compare failed");
    } finally {
      setCompareLoading(false);
    }
  }

  async function addToWatchlist() {
    if (!watchlistAddress.trim()) return;
    setWatchlistError("");
    try {
      const resp = await fetch(`${API_BASE}/watchlist/${encodeURIComponent(watchlistAddress.trim())}`, {
        method: "POST",
      });
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `HTTP ${resp.status}`);
      }
      setWatchlistAddress("");
      await fetchWatchlist();
    } catch (e) {
      setWatchlistError(e?.message || "Failed to add address");
    }
  }

  async function runAssess(overrideTarget) {
    const resolvedTarget = (overrideTarget ?? target).trim();
    if (!resolvedTarget) return;
    setError("");
    setResult(null);
    setLoading(true);
    setLoadingStep(0);

    // Sequential loading animation
    const timer1 = setTimeout(() => setLoadingStep(1), 600);
    const timer2 = setTimeout(() => setLoadingStep(2), 1200);
    const timer3 = setTimeout(() => setLoadingStep(3), 1800);

    try {
      const resp = await fetch(`${API_BASE}/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: resolvedTarget,
          coverage_amount: Number(coverageAmount),
          coverage_days: Number(coverageDays),
        }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
      }
      if (data.error) {
        setError(`> ERROR: ${data.error}`);
        setLoading(false);
        return;
      }
      setTarget(resolvedTarget);
      
      // Wait for animation to finish before showing results
      setTimeout(() => {
        setResult(data);
        setLoading(false);
        fetchHistory();
      }, 2400);
    } catch (e) {
      setError(e?.message || "Request failed");
      setLoading(false);
    }
  }

  const getRiskLevel = (score) => {
    if (score >= 70) return "HIGH RISK";
    if (score >= 40) return "MEDIUM RISK";
    return "LOW RISK";
  };

  const getRiskClass = (score) => {
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
  };

  const scoreClass = (score) => {
    const n = Number(score) || 0;
    if (n >= 70) return "score-high";
    if (n >= 40) return "score-medium";
    return "score-low";
  };

  const aiAnalysis = result?.ai ?? null;
  const riskRows = [
    {
      key: "code_risk",
      label: "CODE RISK",
      score: Number(result?.code_risk?.score ?? 0),
      flags: result?.code_risk?.flags ?? [],
      delay: 0,
    },
    {
      key: "liquidity_risk",
      label: "LIQUIDITY RISK",
      score: Number(result?.liquidity_risk?.score ?? 0),
      flags: result?.liquidity_risk?.flags ?? [],
      delay: 100,
    },
    {
      key: "team_risk",
      label: "TEAM RISK",
      score: Number(result?.team_risk?.score ?? 0),
      flags: result?.team_risk?.flags ?? [],
      delay: 200,
    },
    {
      key: "track_record",
      label: "TRACK RECORD",
      score: Number(result?.track_record?.score ?? 0),
      flags: result?.track_record?.flags ?? [],
      delay: 300,
    },
  ];

  useEffect(() => {
    if (!result) return undefined;
    setBarsArmed(false);
    const timer = window.setTimeout(() => setBarsArmed(true), 100);
    return () => window.clearTimeout(timer);
  }, [result]);

  useEffect(() => {
    if (!result || !scoreRef.current) return undefined;
    return animateScore(Number(result.composite_risk_score) || 0, scoreRef.current);
  }, [result]);

  return (
    <div className="container">
      {/* NAV */}
      <nav className="top-nav" style={{ marginBottom: '40px' }}>
        <div className="logo">ANCHORFI</div>
        <div className="pill-tag">ETHEREUM MAINNET ONLY (v1)</div>
      </nav>

      <div style={{
        width: '100%',
        background: '#111111',
        color: '#f5f0e8',
        height: '32px',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        position: 'relative'
      }}>
        <div style={{
          display: 'flex',
          whiteSpace: 'nowrap',
          animation: 'marquee 25s linear infinite',
          fontSize: '10px',
          fontFamily: "'Courier New', monospace",
          letterSpacing: '2px',
          textTransform: 'uppercase'
        }}>
          <span style={{paddingRight: '60px'}}>
            ETHEREUM MAINNET &nbsp;·&nbsp; POWERED BY GOPLUS + DEFILLAMA + AI 
            &nbsp;·&nbsp; DATA REFRESHED DAILY &nbsp;·&nbsp; NOT FINANCIAL ADVICE 
            &nbsp;·&nbsp; HACKATHON DEMO &nbsp;·&nbsp; ETHEREUM MAINNET &nbsp;·&nbsp; 
            POWERED BY GOPLUS + DEFILLAMA + AI &nbsp;·&nbsp; DATA REFRESHED DAILY 
            &nbsp;·&nbsp; NOT FINANCIAL ADVICE &nbsp;·&nbsp; HACKATHON DEMO
          </span>
        </div>
      </div>

      {/* INPUT SECTION */}
      <section className="brutalist-section lift-card">
        <div className="section-label">INSTANT DEFI RISK ASSESSMENT</div>
        
        <div className="form-group">
          <label className="input-label">CONTRACT OR PROTOCOL</label>
          <input 
            className="field" 
            placeholder="0x... or protocol name e.g. AAVE"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="input-label">COVERAGE $</label>
            <input 
              className="field" 
              style={{ width: '140px' }}
              value={coverageAmount}
              onChange={(e) => setCoverageAmount(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="input-label">DAYS</label>
            <input 
              className="field" 
              style={{ width: '100px' }}
              value={coverageDays}
              onChange={(e) => setCoverageDays(e.target.value)}
            />
          </div>
          <button 
            className="btn-primary" 
            onClick={runAssess}
            disabled={loading || !target}
          >
            ASSESS RISK
          </button>
        </div>

        {error && (
          <div style={{ marginTop: '20px', color: '#c0392b', fontFamily: 'Courier New', fontSize: '12px' }}>
            ERROR: {error}
          </div>
        )}
      </section>

      {/* LOADING STATE OR RESULTS */}
      {error ? (
        <section className="brutalist-section lift-card" id="results" style={{ borderColor: '#c0392b' }}>
          <div style={{
            border: '2px solid #c0392b',
            padding: '20px',
            fontFamily: "'Courier New', monospace",
            fontSize: '12px',
            color: '#c0392b',
            marginTop: '24px'
          }}>
            <div style={{ fontWeight: 900, marginBottom: '8px' }}>ASSESSMENT FAILED</div>
            <div>{error}</div>
            <div style={{ marginTop: '8px', color: '#888', fontSize: '10px' }}>
              CHECK: IS THE BACKEND RUNNING ON PORT 8000? IS VITE PROXY CONFIGURED?
            </div>
          </div>
        </section>
      ) : loading ? (
        <section className="brutalist-section lift-card loading-box">
          <div className="loading-line typewriter">{loadingStep >= 0 && "> FETCHING ON-CHAIN DATA..."}</div>
          <div className="loading-line typewriter">{loadingStep >= 1 && "> RUNNING AI ANALYSIS..."}</div>
          <div className="loading-line typewriter">{loadingStep >= 2 && "> CALCULATING PREMIUM..."}</div>
          {loadingStep >= 3 && <div className="blinking-cursor" style={{ height: '20px' }}></div>}
        </section>
      ) : result ? (
        <section className="brutalist-section lift-card" id="results">
          <div className="results-grid">
            <div className="res-col-left">
              <div className="protocol-label">{result.target || "PROTOCOL"}</div>
              <div className="score-large">
                <span ref={scoreRef}>0</span>
                <span className="score-base">/100</span>
              </div>
              <div className={`risk-badge ${getRiskClass(result.composite_risk_score)}`}>
                {getRiskLevel(result.composite_risk_score)}
              </div>
              <div className="premium-text">
                EST. PREMIUM: ${formatUsdc(result.premium_usdc)} USDC / {coverageDays} DAYS
              </div>
            </div>
            <div className="res-col-right">
              <div className="section-label" style={{ marginBottom: '12px', fontSize: '10px' }}>RISK BREAKDOWN</div>
              
              {riskRows.map((risk) => (
                <div className="risk-row" key={risk.key}>
                  <div className="risk-row-header">
                    <span>{risk.label}</span>
                    <span>{risk.score}</span>
                  </div>
                  <div className="bar-track">
                    <div 
                      className={`bar-fill ${getRiskClass(risk.score)}`} 
                      style={{
                        width: barsArmed ? `${(risk.score / 100) * 100}%` : "0%",
                        transitionDelay: `${risk.delay}ms`,
                      }}
                    />
                  </div>
                  {risk.flags.length > 0 ? (
                    <div className="flags-row">
                      {risk.flags.slice(0, 4).map((flag) => (
                        <span
                          key={`${risk.key}-${flag}`}
                          className={`flag ${risk.score > 60 ? "high" : ""}`}
                        >
                          {String(flag).toUpperCase()}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <hr className="separator" />

          <div>
            <div className="ai-header">
              <div className="section-label" style={{ fontSize: '10px', marginBottom: '0' }}>GROQ RISK ANALYSIS</div>
              {aiAnalysis?.confidence ? (
                <div className={`confidence-pill ${String(aiAnalysis.confidence).toLowerCase()}`}>
                  CONFIDENCE: {String(aiAnalysis.confidence).toUpperCase()}
                </div>
              ) : null}
            </div>
            {aiAnalysis ? (
              <>
                <div className="ai-text">{aiAnalysis.summary}</div>
                {Array.isArray(aiAnalysis.top_risks) && aiAnalysis.top_risks.length > 0 ? (
                  <div className="top-risks-list">
                    {aiAnalysis.top_risks.slice(0, 3).map((risk) => (
                      <div className="top-risk-line" key={risk}>
                        <span className="top-risk-prefix">&gt;</span> {String(risk).toUpperCase()}
                      </div>
                    ))}
                  </div>
                ) : null}
                <div className="verdict">
                  VERDICT: {aiAnalysis.recommended_action || "UNKNOWN"}
                </div>
              </>
            ) : (
              <div className="ai-missing">&gt; GROQ ANALYSIS UNAVAILABLE — GROQ API KEY MISSING</div>
            )}
          </div>
        </section>
      ) : (
        <section className="brutalist-section lift-card empty-state" id="results">
          <pre>{`┌─────────────────────────────────────────────────────┐
│                                                     │
│   > AWAITING INPUT_                                 │
│                                                     │
│   PASTE A CONTRACT ADDRESS OR PROTOCOL NAME ABOVE   │
│   TO GENERATE A RISK ASSESSMENT.                    │
│                                                     │
└─────────────────────────────────────────────────────┘`}</pre>
        </section>
      )}

      {/* PROTOCOL COMPARISON SECTION */}
      <section className="brutalist-section lift-card" style={{ marginTop: '40px' }}>
        <div className="section-label">PROTOCOL COMPARISON</div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '12px', alignItems: 'flex-end', marginBottom: '20px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="input-label">PROTOCOL 1</label>
            <input 
              className="field" 
              value={compareTargets[0]}
              onChange={(e) => {
                const next = [...compareTargets];
                next[0] = e.target.value;
                setCompareTargets(next);
              }}
              placeholder="AAVE"
            />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="input-label">PROTOCOL 2</label>
            <input 
              className="field" 
              value={compareTargets[1]}
              onChange={(e) => {
                const next = [...compareTargets];
                next[1] = e.target.value;
                setCompareTargets(next);
              }}
              placeholder="COMPOUND"
            />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="input-label">PROTOCOL 3 (OPT)</label>
            <input 
              className="field" 
              value={compareTargets[2]}
              onChange={(e) => {
                const next = [...compareTargets];
                next[2] = e.target.value;
                setCompareTargets(next);
              }}
              placeholder="UNISWAP"
            />
          </div>
          <button 
            className="btn-primary" 
            onClick={runCompare}
            disabled={compareLoading}
            style={{ height: '42px' }}
          >
            {compareLoading ? "COMPARING..." : "COMPARE"}
          </button>
        </div>
        
        {compareError && (
          <div style={{ color: '#c0392b', fontFamily: 'Courier New', fontSize: '12px', marginBottom: '12px' }}>
            ERROR: {compareError}
          </div>
        )}
      </section>

      {/* COMPARE RESULTS */}
      {compareResult?.items && compareResult.items.length > 0 && (
        <section id="compare-results" className="brutalist-section lift-card" style={{ marginTop: '24px' }}>
          <div className="section-label">COMPARISON RESULTS</div>
          <div style={{ marginBottom: '20px', fontFamily: 'Courier New', fontSize: '11px', color: '#888' }}>
            {compareResult.winner_target && (
              <>LOWEST RISK PROTOCOL: <span style={{ color: '#111', fontWeight: 'bold' }}>{compareResult.winner_target}</span></>
            )}
          </div>
          
          <div className="compare-grid" style={{ gridTemplateColumns: compareResult.items.length === 2 ? '1fr 1fr' : '1fr 1fr 1fr' }}>
            {compareResult.items.map((item) => (
              <div
                className="compare-card"
                key={item.report_uuid}
                style={{ background: item.report_uuid === compareResult.winner_report_uuid ? 'rgba(1, 1, 1, 0.05)' : 'transparent' }}
              >
                {item.report_uuid === compareResult.winner_report_uuid && (
                  <div style={{
                    position: 'absolute',
                    top: '-12px',
                    right: '12px',
                    background: '#111',
                    color: '#f5f0e8',
                    padding: '3px 8px',
                    fontSize: '9px',
                    fontWeight: 'bold',
                    fontFamily: 'Courier New',
                    textTransform: 'uppercase',
                    letterSpacing: '1px'
                  }}>
                    WINNER
                  </div>
                )}
                
                <div style={{ fontFamily: 'Courier New', fontSize: '11px', color: '#888', marginBottom: '8px', textTransform: 'uppercase' }}>
                  {item.target}
                </div>
                <div style={{ fontSize: '32px', fontWeight: '900', fontFamily: 'Courier New', marginBottom: '8px' }}>
                  {item.composite_risk_score}
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 8px',
                    fontSize: '9px',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    background: item.composite_risk_score >= 70 ? '#c0392b' : item.composite_risk_score >= 40 ? '#888' : '#111',
                    color: '#f5f0e8',
                    fontFamily: 'Courier New'
                  }}>
                    {getRiskLevel(item.composite_risk_score)}
                  </span>
                </div>
                <div style={{ fontSize: '11px', marginBottom: '12px', lineHeight: '1.6' }}>
                  <strong>Premium:</strong> ${formatUsdc(item.premium_usdc)} USDC
                </div>
                {item.ai ? (
                  <div style={{ fontSize: '10px', borderTop: '1px solid #ddd9d0', paddingTop: '8px', marginTop: '8px' }}>
                    <strong style={{ color: '#111' }}>Action:</strong> <span style={{ color: '#888' }}>{item.ai?.recommended_action || "—"}</span>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* WATCHLIST SECTION */}
      <section className="brutalist-section lift-card" style={{ marginTop: '40px' }}>
        <div className="section-label">DEFI ADDRESS WATCHLIST</div>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label className="input-label">ETHEREUM ADDRESS</label>
            <input 
              className="field" 
              value={watchlistAddress}
              onChange={(e) => setWatchlistAddress(e.target.value)}
              placeholder="0x... or contract name"
            />
          </div>
          <button 
            className="btn-primary"
            onClick={addToWatchlist}
            style={{ height: '42px' }}
          >
            ADD
          </button>
          <button 
            className="btn-primary"
            onClick={fetchWatchlist}
            style={{ height: '42px', background: '#ddd9d0', color: '#111' }}
          >
            REFRESH
          </button>
        </div>
        
        {watchlistError && (
          <div style={{ color: '#c0392b', fontFamily: 'Courier New', fontSize: '12px', marginBottom: '12px' }}>
            ERROR: {watchlistError}
          </div>
        )}

        <div>
          {watchlistLoading ? (
            <div style={{ fontFamily: 'Courier New', fontSize: '12px', color: '#888' }}>
              REFRESHING WATCHLIST...
            </div>
          ) : watchlistItems.length === 0 ? (
            <div style={{ fontFamily: 'Courier New', fontSize: '12px', color: '#888' }}>
              NO ADDRESSES MONITORED YET
            </div>
          ) : (
            <div className="watchlist-list">
              {watchlistItems.map((item) => (
                <div
                  className="watchlist-item"
                  key={item.address}
                  style={{ background: item.risk_increased ? 'rgba(192, 57, 43, 0.08)' : 'transparent' }}
                >
                  <div>
                    <div style={{ fontFamily: 'Courier New', fontSize: '11px', marginBottom: '4px', color: '#111', fontWeight: 'bold' }}>
                      {item.address}
                    </div>
                    <div style={{ fontFamily: 'Courier New', fontSize: '9px', color: '#888' }}>
                      PREV: {item.previous_score ?? "—"} | NOW: {item.current_score ?? "—"}
                      {item.score_delta !== null && (
                        <span style={{ marginLeft: '8px', color: item.risk_increased ? '#c0392b' : '#111', fontWeight: 'bold' }}>
                          {item.score_delta > 0 ? '+' : ''}{item.score_delta}
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '3px 8px',
                      fontSize: '8px',
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      background: item.risk_increased ? '#c0392b' : '#111',
                      color: '#f5f0e8',
                      fontFamily: 'Courier New',
                      letterSpacing: '0.5px'
                    }}>
                      {item.risk_increased ? '⚠ RISK UP' : '✓ STABLE'}
                    </span>
                    {item.report_uuid && (
                      <a 
                        href={`${API_BASE}/report/${item.report_uuid}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          border: '1px solid #111',
                          padding: '4px 8px',
                          fontSize: '9px',
                          fontWeight: 'bold',
                          fontFamily: 'Courier New',
                          textDecoration: 'none',
                          color: '#111',
                          background: 'transparent',
                          textTransform: 'uppercase',
                          cursor: 'pointer',
                          letterSpacing: '0.5px'
                        }}
                      >
                        REPORT
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* RECENT ASSESSMENTS TABLE */}
      <section style={{ marginTop: '40px' }}>
        <div className="table-header">
          <div className="section-label" style={{ margin: 0 }}>RECENT ASSESSMENTS</div>
          <div className="section-label" style={{ margin: 0 }}>CACHED DAILY</div>
        </div>
        
        <table className="brutalist-table">
          <thead>
            <tr>
              <th>TARGET</th>
              <th>SCORE</th>
              <th>PREMIUM</th>
              <th>DATE</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, i) => (
              <tr
                key={item.id ?? item.report_uuid ?? `${item.target}-${i}`}
                className="history-row"
                onClick={() => {
                  setTarget(item.target || "");
                  void runAssess(item.target || "");
                }}
              >
                <td className="target-col">{item.target}</td>
                <td className={`score-col ${scoreClass(item.composite_risk_score)}`}>
                  {item.composite_risk_score}
                </td>
                <td>{formatUsdc(item.premium_usdc)} USDC</td>
                <td>{formatHistoryDate(item)}</td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', color: '#888' }}>No recent assessments found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <footer className="footer-bar mono">
        <div>ANCHORFI v0.1.0 — HASHKEY CHAIN HORIZON HACKATHON 2026</div>
        <div>ANCHORFI IS A DEMO. NO FUNDS, POLICIES, OR GUARANTEES.</div>
      </footer>
    </div>
  );
}

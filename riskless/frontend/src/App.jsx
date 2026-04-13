import { useEffect, useMemo, useState } from "react";

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

export default function App() {
  const [target, setTarget] = useState("");
  const [coverageAmount, setCoverageAmount] = useState(10000);
  const [coverageDays, setCoverageDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0); // 0, 1, 2, 3 (finished)
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

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

  async function runAssess() {
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
    if (score > 60) return "HIGH RISK";
    if (score > 30) return "MEDIUM";
    return "LOW RISK";
  };

  const getRiskClass = (score) => {
    if (score > 60) return "high";
    if (score > 30) return "medium";
    return "low";
  };

  return (
    <div className="container">
      {/* NAV */}
      <nav className="top-nav" style={{ marginBottom: '40px' }}>
        <div className="logo">ANCHORFI</div>
        <div className="pill-tag">ETHEREUM MAINNET ONLY (v1)</div>
      </nav>

      {/* INPUT SECTION */}
      <section className="brutalist-section">
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
      {loading ? (
        <section className="brutalist-section loading-box">
          <div className="loading-line typewriter">{loadingStep >= 0 && "> FETCHING ON-CHAIN DATA..."}</div>
          <div className="loading-line typewriter">{loadingStep >= 1 && "> RUNNING AI ANALYSIS..."}</div>
          <div className="loading-line typewriter">{loadingStep >= 2 && "> CALCULATING PREMIUM..."}</div>
          {loadingStep >= 3 && <div className="blinking-cursor" style={{ height: '20px' }}></div>}
        </section>
      ) : result ? (
        <section className="brutalist-section" id="results">
          <div className="results-grid">
            <div className="res-col-left">
              <div className="protocol-label">{result.target || "PROTOCOL"}</div>
              <div className="score-large">
                {result.composite_risk_score}
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
              
              {[
                { label: 'CODE RISK', value: result.raw_signals?.defi?.code_quality_score || 0 },
                { label: 'LIQUIDITY RISK', value: result.raw_signals?.defi?.liquidity_score || 0 },
                { label: 'TEAM RISK', value: result.raw_signals?.defi?.team_score || 0 },
                { label: 'TRACK RECORD', value: result.raw_signals?.defi?.maturity_score || 0 }
              ].map((risk) => (
                <div className="risk-row" key={risk.label}>
                  <div className="risk-row-header">
                    <span>{risk.label}</span>
                    <span>{risk.value}</span>
                  </div>
                  <div className="bar-track">
                    <div 
                      className={`bar-fill ${getRiskClass(risk.value)}`} 
                      style={{ width: `${risk.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <hr className="separator" />

          <div>
            <div className="section-label" style={{ fontSize: '10px', marginBottom: '12px' }}>AI ASSESSMENT</div>
            <div className="ai-text">
              {result.ai?.summary || "No AI summary available."}
            </div>
            <div className="verdict">
              VERDICT: {result.ai?.recommended_action || "UNKNOWN"}
            </div>
          </div>
        </section>
      ) : null}

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
              <tr key={i}>
                <td className="target-col">{item.target}</td>
                <td className="score-col">{item.composite_risk_score}</td>
                <td>{formatUsdc(item.premium_usdc)} USDC</td>
                <td>{new Date(item.created_at).toLocaleDateString()}</td>
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

      <footer style={{ marginTop: '60px', fontSize: '10px', color: '#888', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>
        ANCHORFI IS A HACKATHON DEMO. NO FUNDS, POLICIES, OR GUARANTEES.
      </footer>
    </div>
  );
}

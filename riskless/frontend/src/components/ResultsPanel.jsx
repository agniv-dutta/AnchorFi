import { useState } from "react";

import AIPanel from "./AIPanel";
import RiskGauge from "./RiskGauge";
import RiskBars from "./RiskBars";
import RiskRadarChart from "./RadarChart";
import TimelineChart from "./TimelineChart";

export default function ResultsPanel({ assessResult, animatedScore, history }) {
  const [shareFeedback, setShareFeedback] = useState(false);
  const freshness = assessResult?.data_freshness || {};
  const partialFlags = freshness.partial_data_flags || [];

  const handleShare = async () => {
    const url = `${window.location.origin}/report/${assessResult.id}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      const el = document.createElement("textarea");
      el.value = url;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setShareFeedback(true);
    setTimeout(() => setShareFeedback(false), 2000);
  };

  return (
    <section className="card results-card">
      <div className="results-grid">
        <RiskGauge
          target={assessResult.target}
          score={assessResult.composite_risk_score}
          premium={assessResult.premium}
          coverageDays={assessResult.coverage_days}
          animatedScore={animatedScore}
        />
        <RiskBars assessResult={assessResult} />
      </div>
      <hr className="sep" />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
        <span className={`meta-pill ${assessResult.cached ? "meta-pill-muted" : "meta-pill-ok"}`}>
          {assessResult.cached ? "SOURCE: CACHED" : "SOURCE: LIVE"}
        </span>
        <span className="meta-pill meta-pill-muted">
          AGE: {freshness.source_age_seconds ?? 0}s
        </span>
        {partialFlags.length ? (
          <span className="meta-pill meta-pill-warn">DATA: PARTIAL ({partialFlags.length})</span>
        ) : (
          <span className="meta-pill meta-pill-ok">DATA: COMPLETE</span>
        )}
      </div>
      <AIPanel ai={assessResult.ai} />
      <div style={{ marginTop: 12 }}>
        <button className={`btn btn-sm ${shareFeedback ? "share-copied" : ""}`} onClick={handleShare}>
          {shareFeedback ? "LINK COPIED ✓" : "SHARE REPORT"}
        </button>
      </div>
      <RiskRadarChart assessResult={assessResult} />
      <TimelineChart history={history} />
    </section>
  );
}

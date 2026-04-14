import AIPanel from "./AIPanel";
import RiskGauge from "./RiskGauge";
import RiskBars from "./RiskBars";
import RiskRadarChart from "./RadarChart";
import TimelineChart from "./TimelineChart";

export default function ResultsPanel({ assessResult, animatedScore, history, onShare, copied }) {
  return (
    <section className="card">
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
      <AIPanel ai={assessResult.ai} />
      <div style={{ marginTop: 12 }}>
        <button className="btn btn-sm" onClick={() => onShare(assessResult.id)}>SHARE REPORT</button>
        {copied ? <span className="k-mono" style={{ marginLeft: 10, fontSize: 10 }}>LINK COPIED</span> : null}
      </div>
      <RiskRadarChart assessResult={assessResult} />
      <TimelineChart history={history} />
    </section>
  );
}

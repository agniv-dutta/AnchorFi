function barColor(score) {
  if (score >= 70) return "#c0392b";
  if (score >= 40) return "#888";
  return "#2d7a4f";
}

export default function RiskBars({ assessResult }) {
  const rows = [
    ["CODE RISK", assessResult.code_risk],
    ["LIQUIDITY RISK", assessResult.liquidity_risk],
    ["TEAM RISK", assessResult.team_risk],
    ["TRACK RECORD", assessResult.track_record],
  ];

  return (
    <div>
      {rows.map(([label, cat], idx) => (
        <div key={label} style={{ marginBottom: 10 }}>
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 28px", gap: 8, alignItems: "center" }}>
            <div className="k-mono" style={{ fontSize: 10, letterSpacing: 1, color: "#888" }}>{label}</div>
            <div style={{ height: 8, background: "#ddd9d0", border: "1px solid #c8c2b8" }}>
              <div style={{ width: `${cat.score}%`, height: "100%", background: barColor(cat.score), transition: `width 600ms ${idx * 100}ms` }} />
            </div>
            <div className="k-mono" style={{ fontSize: 12, fontWeight: 900, textAlign: "right" }}>{cat.score}</div>
          </div>
          <div style={{ marginTop: 2 }}>
            {(cat.flags || []).map((flag) => (
              <span key={`${label}-${flag}`} style={{ border: `1px solid ${cat.score >= 70 ? "#c0392b" : "#111"}`, color: cat.score >= 70 ? "#c0392b" : "#111", fontFamily: "'Courier New', monospace", fontSize: 9, padding: "2px 6px", display: "inline-block", margin: 2, textTransform: "uppercase", letterSpacing: ".5px" }}>{flag}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

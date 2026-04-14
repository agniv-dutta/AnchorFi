function verdictColor(action) {
  if (action === "Safe to insure") return "#2d7a4f";
  if (action === "High risk — avoid") return "#c0392b";
  return "#888";
}

function confidenceColor(confidence) {
  if (confidence === "High") return "#2d7a4f";
  if (confidence === "Low") return "#c0392b";
  return "#888";
}

export default function AIPanel({ ai }) {
  const color = confidenceColor(ai?.confidence || "Medium");
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div className="k-label" style={{ fontSize: 10 }}>AI ASSESSMENT</div>
        <div style={{ border: `1px solid ${color}`, color, fontFamily: "'Courier New', monospace", fontSize: 9, textTransform: "uppercase", letterSpacing: 1, padding: "2px 8px" }}>CONFIDENCE: {ai?.confidence || "Low"}</div>
      </div>
      <p style={{ fontFamily: "Georgia, serif", fontSize: 15, lineHeight: 1.8, color: "#111", maxWidth: 640 }}>{ai?.summary || "No summary available."}</p>
      {(ai?.top_risks || []).map((risk) => (
        <div key={risk} style={{ fontFamily: "'Courier New', monospace", fontSize: 11, fontWeight: 700 }}><span style={{ color: "#c0392b" }}>&gt;</span> {String(risk).toUpperCase()}</div>
      ))}
      {(ai?.positive_signals || []).map((signal) => (
        <div key={signal} style={{ fontFamily: "'Courier New', monospace", fontSize: 11 }}><span style={{ color: "#2d7a4f" }}>+</span> {String(signal).toUpperCase()}</div>
      ))}
      {ai?.underwriter_note ? <div style={{ marginTop: 10, fontFamily: "Georgia, serif", fontStyle: "italic", fontSize: 13, color: "#555" }}>UNDERWRITER NOTE: "{ai.underwriter_note}"</div> : null}
      <div style={{ marginTop: 12, fontFamily: "'Courier New', monospace", fontSize: 11, fontWeight: 900, textTransform: "uppercase", color: verdictColor(ai?.recommended_action) }}>
        VERDICT: {ai?.recommended_action || "Insure with caution"}
      </div>
    </div>
  );
}

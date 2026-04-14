export default function EmptyState() {
  return (
    <div className="card" style={{ borderStyle: "dashed", borderColor: "#bbb6ad", textAlign: "center", padding: 60, color: "#888" }}>
      <div className="k-mono">&gt; AWAITING INPUT_</div>
      <div className="k-mono" style={{ marginTop: 12 }}>PASTE A CONTRACT ADDRESS OR PROTOCOL NAME</div>
      <div className="k-mono">ABOVE TO GENERATE A RISK ASSESSMENT.</div>
    </div>
  );
}

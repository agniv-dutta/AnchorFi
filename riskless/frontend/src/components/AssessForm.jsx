export default function AssessForm({
  currentTarget,
  setCurrentTarget,
  coverageAmount,
  setCoverageAmount,
  coverageDays,
  setCoverageDays,
  onAssess,
  onDemo,
}) {
  return (
    <section className="card">
      <div className="k-label" style={{ marginBottom: 10 }}>INSTANT DEFI RISK ASSESSMENT</div>
      <input className="input" value={currentTarget} onChange={(e) => setCurrentTarget(e.target.value)} placeholder="0x... or protocol name e.g. AAVE" />
      <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap", alignItems: "end" }}>
        <div>
          <div className="k-label" style={{ marginBottom: 6 }}>Coverage</div>
          <input className="input" style={{ width: 140 }} type="number" value={coverageAmount} onChange={(e) => setCoverageAmount(Number(e.target.value || 0))} />
        </div>
        <div>
          <div className="k-label" style={{ marginBottom: 6 }}>Days</div>
          <input className="input" style={{ width: 100 }} type="number" value={coverageDays} onChange={(e) => setCoverageDays(Number(e.target.value || 0))} />
        </div>
        <button className="btn" onClick={onAssess}>ASSESS RISK</button>
      </div>
      <div className="k-label" style={{ marginTop: 14, marginBottom: 8 }}>DEMO CASES</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="btn btn-sm" onClick={() => onDemo("aave")}>TRY: AAVE</button>
        <button className="btn btn-sm" onClick={() => onDemo("compound")}>TRY: COMPOUND</button>
        <button className="btn btn-sm" onClick={() => onDemo("0x098B716B8Aaf21512996dC57EB0615e2383E2f96")}>TRY: RONIN BRIDGE EXPLOITER</button>
      </div>
    </section>
  );
}

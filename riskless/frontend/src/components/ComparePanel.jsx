import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function badge(score) {
  if (score >= 70) return ["HIGH RISK", "risk-high"];
  if (score >= 40) return ["MEDIUM RISK", "risk-medium"];
  return ["LOW RISK", "risk-low"];
}

export default function ComparePanel({ compare, setCompare, onCompare, compareResults }) {
  const chartData = (compareResults?.results || []).map((r) => ({
    name: r.target,
    code: r.code_risk?.score || 0,
    liquidity: r.liquidity_risk?.score || 0,
    team: r.team_risk?.score || 0,
    track: r.track_record?.score || 0,
  }));

  return (
    <section className="card">
      <div className="k-label" style={{ marginBottom: 10 }}>PROTOCOL COMPARISON</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 8, alignItems: "end" }}>
        <input className="input" placeholder="PROTOCOL 1" value={compare.p1} onChange={(e) => setCompare((v) => ({ ...v, p1: e.target.value }))} />
        <input className="input" placeholder="PROTOCOL 2" value={compare.p2} onChange={(e) => setCompare((v) => ({ ...v, p2: e.target.value }))} />
        <input className="input" placeholder="PROTOCOL 3 (OPT)" value={compare.p3} onChange={(e) => setCompare((v) => ({ ...v, p3: e.target.value }))} />
        <button className="btn" onClick={onCompare}>COMPARE</button>
      </div>

      {compareResults?.results?.length ? (
        <>
          <div className="compare-grid" style={{ marginTop: 12 }}>
            {compareResults.results.map((item) => {
              const [label, cls] = badge(item.composite_risk_score || 100);
              const safest = Boolean(item.is_safest);
              return (
                <div key={`${item.id}-${item.target}`} className={`compare-card ${safest ? "compare-safe" : ""}`}>
                  {safest ? <div className="safe-badge">SAFEST</div> : null}
                  <div className="k-mono" style={{ fontSize: 12, textTransform: "uppercase", marginBottom: 4 }}>{item.target}</div>
                  <div className="k-mono" style={{ fontSize: 48, fontWeight: 900, lineHeight: 1 }}>{item.composite_risk_score}</div>
                  <span className={`risk-badge ${cls}`}>{label}</span>
                  <div className="k-mono" style={{ fontSize: 11, marginTop: 8 }}>PREMIUM: ${item.premium}</div>
                  <div style={{ marginTop: 8 }}>
                    {[item.code_risk, item.liquidity_risk, item.team_risk, item.track_record].map((cat, idx) => (
                      <div key={idx} style={{ display: "grid", gridTemplateColumns: "1fr 24px", gap: 6, marginBottom: 3 }}>
                        <div style={{ height: 6, border: "1px solid #c8c2b8", background: "#ddd9d0" }}><div style={{ height: "100%", width: `${cat?.score || 0}%`, background: "#111" }} /></div>
                        <div className="k-mono" style={{ fontSize: 10 }}>{cat?.score || 0}</div>
                      </div>
                    ))}
                  </div>
                  <p style={{ marginTop: 8, fontFamily: "Georgia, serif", fontSize: 12 }}>{String(item.ai?.summary || "").split(".")[0]}.</p>
                </div>
              );
            })}
          </div>
          <div style={{ width: "100%", height: 280, marginTop: 12 }}>
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid stroke="#ddd9d0" />
                <XAxis dataKey="name" tick={{ fontFamily: "'Courier New', monospace", fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontFamily: "'Courier New', monospace", fontSize: 10 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="code" fill="#111" />
                <Bar dataKey="liquidity" fill="#555" />
                <Bar dataKey="team" fill="#888" />
                <Bar dataKey="track" fill="#bbb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : null}
    </section>
  );
}

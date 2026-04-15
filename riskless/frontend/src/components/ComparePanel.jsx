import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function badge(score) {
  if (score >= 70) return ["HIGH RISK", "risk-high"];
  if (score >= 40) return ["MEDIUM RISK", "risk-medium"];
  return ["LOW RISK", "risk-low"];
}

export default function ComparePanel({ compare, setCompare, onCompare, compareResults, compareLoading, compareError }) {
  const results = Array.isArray(compareResults) ? compareResults : [];
  const chartData = [
    { name: "Code", ...Object.fromEntries(results.map((r) => [r.target, r.code_risk?.score ?? 0])) },
    { name: "Liquidity", ...Object.fromEntries(results.map((r) => [r.target, r.liquidity_risk?.score ?? 0])) },
    { name: "Team", ...Object.fromEntries(results.map((r) => [r.target, r.team_risk?.score ?? 0])) },
    { name: "Track", ...Object.fromEntries(results.map((r) => [r.target, r.track_record?.score ?? 0])) },
  ];
  const colors = ["#111", "#888", "#c0392b"];

  return (
    <section className="card">
      <div className="section-label">PROTOCOL COMPARISON</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 8, alignItems: "end" }}>
        <input className="input" placeholder="PROTOCOL 1" value={compare.p1} onChange={(e) => setCompare((v) => ({ ...v, p1: e.target.value }))} />
        <input className="input" placeholder="PROTOCOL 2" value={compare.p2} onChange={(e) => setCompare((v) => ({ ...v, p2: e.target.value }))} />
        <input className="input" placeholder="PROTOCOL 3 (OPT)" value={compare.p3} onChange={(e) => setCompare((v) => ({ ...v, p3: e.target.value }))} />
        <button className="btn" onClick={onCompare} disabled={compareLoading}>{compareLoading ? "COMPARING..." : "COMPARE"}</button>
      </div>

      {compareError ? (
        <div style={{ marginTop: 10, border: "1px solid #c0392b", color: "#c0392b", padding: "8px 10px", fontFamily: "'Courier New', monospace", fontSize: 10 }}>
          {compareError}
        </div>
      ) : null}

      {results.length ? (
        <>
          <div className="compare-grid" style={{ marginTop: 20 }}>
            {results.map((item) => {
              const [label, cls] = badge(item.composite_risk_score || 100);
              const safest = Boolean(item.is_safest);
              return (
                <div key={item.target} className={`compare-card ${safest ? "compare-safe" : ""}`}>
                  {safest && (
                    <div
                      style={{
                        position: "absolute",
                        top: "-1px",
                        right: "-1px",
                        background: "#2d7a4f",
                        color: "#f5f0e8",
                        fontFamily: "'Courier New',monospace",
                        fontSize: "9px",
                        fontWeight: 900,
                        letterSpacing: "1px",
                        padding: "3px 8px",
                        textTransform: "uppercase",
                      }}
                    >
                      SAFEST
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 6, marginBottom: 6, flexWrap: "wrap" }}>
                    <span className={`meta-pill ${item.cached ? "meta-pill-muted" : "meta-pill-ok"}`}>
                      {item.cached ? "cached" : "live"}
                    </span>
                    {item.ai?.ai_provider ? (
                      <span className={`meta-pill ${item.ai.ai_provider === "deterministic_fallback" ? "meta-pill-warn" : "meta-pill-ok"}`}>
                        {String(item.ai.ai_provider).replaceAll("_", " ")}
                      </span>
                    ) : null}
                    {item.data_freshness?.partial_data_flags?.length ? (
                      <span className="meta-pill meta-pill-warn">partial data ({item.data_freshness.partial_data_flags.length})</span>
                    ) : (
                      <span className="meta-pill meta-pill-ok">complete data</span>
                    )}
                  </div>
                  {item.data_freshness?.partial_data_flags?.length ? (
                    <div style={{ fontFamily: "'Courier New', monospace", fontSize: 9, color: "#a05a50", marginBottom: 8 }}>
                      {item.data_freshness.partial_data_flags.slice(0, 2).map((f) => String(f).replaceAll("_", " ")).join(" | ")}
                    </div>
                  ) : null}
                  <div style={{ fontFamily: "'Courier New'", fontSize: "11px", color: "#888", letterSpacing: "2px", textTransform: "uppercase", marginBottom: "6px" }}>{item.target}</div>
                  <div style={{ fontFamily: "'Courier New'", fontSize: "56px", fontWeight: 900, lineHeight: 1, color: "#111" }}>
                    {item.composite_risk_score}
                  </div>
                  <div style={{ fontFamily: "'Courier New'", fontSize: "10px", color: "#888", marginBottom: "12px" }}>/100</div>
                  <span className={`risk-badge ${cls}`}>{label}</span>
                  {[
                    "code_risk",
                    "liquidity_risk",
                    "team_risk",
                    "track_record",
                  ].map((key) => (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                      <div style={{ fontFamily: "'Courier New'", fontSize: "8px", color: "#aaa", width: "60px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                        {key.replace("_risk", "").replace("_", " ")}
                      </div>
                      <div style={{ flex: 1, height: "4px", background: "#ddd9d0" }}>
                        <div
                          style={{
                            height: "4px",
                            width: item[key] ? `${item[key].score}%` : "0%",
                            background: item[key]?.score < 40 ? "#2d7a4f" : item[key]?.score < 70 ? "#888" : "#c0392b",
                          }}
                        />
                      </div>
                      <div style={{ fontFamily: "'Courier New'", fontSize: "10px", fontWeight: 900, color: "#111", minWidth: "20px", textAlign: "right" }}>
                        {item[key]?.score ?? 0}
                      </div>
                    </div>
                  ))}
                  <div style={{ fontFamily: "Georgia,serif", fontSize: "11px", color: "#555", lineHeight: 1.6, marginTop: "10px", borderTop: "1px solid #ddd9d0", paddingTop: "8px" }}>
                    {(item.ai?.summary ? `${String(item.ai.summary).split(".")[0]}.` : "—")}
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ width: "100%", height: 240, marginTop: 16 }}>
            <ResponsiveContainer>
              <BarChart data={chartData} style={{ fontFamily: "'Courier New'", fontSize: "10px" }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ddd9d0" />
                <XAxis dataKey="name" tick={{ fill: "#888", fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#888", fontSize: 10 }} />
                <Tooltip contentStyle={{ fontFamily: "'Courier New'", fontSize: "11px", border: "2px solid #111", background: "#f5f0e8", borderRadius: 0 }} />
                <Legend wrapperStyle={{ fontFamily: "'Courier New'", fontSize: "10px" }} />
                {results.map((r, i) => (
                  <Bar key={r.target} dataKey={r.target} fill={colors[i] || "#111"} radius={0} maxBarSize={40} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : null}
    </section>
  );
}

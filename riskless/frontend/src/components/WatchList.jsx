function riskBadge(score) {
  if (score >= 70) return ["HIGH RISK", "risk-high"];
  if (score >= 40) return ["MEDIUM RISK", "risk-medium"];
  return ["LOW RISK", "risk-low"];
}

export default function WatchList({ watchAddress, setWatchAddress, watchlist, onAdd, onRefresh, onRemove }) {
  return (
    <section className="card">
      <div className="section-label">DEFI ADDRESS WATCHLIST</div>
      <div style={{ display: "flex", gap: 8, alignItems: "end", flexWrap: "wrap" }}>
        <input className="input" style={{ flex: 1 }} value={watchAddress} onChange={(e) => setWatchAddress(e.target.value)} placeholder="0x..." />
        <button className="btn" onClick={onAdd}>ADD</button>
        <button className="btn" onClick={onRefresh}>REFRESH</button>
      </div>
      <div style={{ marginTop: 12 }}>
        {!watchlist.length ? <div className="k-mono" style={{ color: "#888", fontSize: 11 }}>NO ADDRESSES MONITORED YET</div> : null}
        {watchlist.map((item) => {
          const [label, cls] = riskBadge(item.latest_score || 0);
          const raw = item.last_checked_at || item.timestamp;
          const d = new Date(typeof raw === "number" ? raw * 1000 : raw);
          const when = Number.isNaN(d.getTime()) ? "—" : d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
          return (
            <div className="watch-row" key={item.address}>
              <div>
                <div className="k-mono" style={{ fontSize: 12 }}>{item.address}</div>
                <div className="k-mono" style={{ fontSize: 10, color: "#888" }}>LAST CHECKED: {when}</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className={`risk-badge ${cls}`}>{label}</span>
                {item.risk_increased ? <span className="flag-up">▲ RISK INCREASED</span> : null}
                {item.risk_change_pct !== undefined && item.risk_change_pct !== null ? (
                  <span className={`meta-pill ${item.risk_change_pct >= 0 ? "meta-pill-warn" : "meta-pill-ok"}`}>
                    {item.risk_change_pct >= 0 ? "+" : ""}{item.risk_change_pct}%
                  </span>
                ) : null}
                <button className="btn btn-sm" style={{ borderColor: "#888", color: "#111", background: "#f5f0e8" }} onClick={() => onRemove(item.address)}>×</button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

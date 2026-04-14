export default function RecentTable({ history, onPick }) {
  return (
    <section className="card">
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <div className="k-label" style={{ margin: 0 }}>RECENT ASSESSMENTS</div>
        <div className="k-label" style={{ margin: 0 }}>CACHED DAILY</div>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>TARGET</th>
            <th>SCORE</th>
            <th>PREMIUM</th>
            <th>DATE</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => {
            const raw = item.created_at || item.timestamp;
            const d = new Date(typeof raw === "number" ? raw * 1000 : raw);
            const display = Number.isNaN(d.getTime()) ? "—" : d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
            const cls = item.composite_risk_score >= 70 ? "#c0392b" : item.composite_risk_score >= 40 ? "#888" : "#111";
            return (
              <tr key={item.id} onClick={() => onPick(item.target)} style={{ cursor: "pointer" }}>
                <td>{item.target}</td>
                <td style={{ color: cls, fontWeight: 900 }}>{item.composite_risk_score}</td>
                <td>${item.premium}</td>
                <td>{display}</td>
              </tr>
            );
          })}
          {!history.length ? (
            <tr>
              <td colSpan={4} style={{ textAlign: "center", color: "#888" }}>No recent assessments found.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}

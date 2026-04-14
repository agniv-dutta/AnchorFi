import { Line, LineChart, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";

export default function TimelineChart({ history }) {
  if (!history || history.length < 2) return null;
  const data = [...history].reverse().map((item) => {
    const raw = item.created_at || item.timestamp;
    const d = new Date(typeof raw === "number" ? raw * 1000 : raw);
    return {
      date: Number.isNaN(d.getTime()) ? "—" : d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      score: item.composite_risk_score,
    };
  });

  return (
    <div style={{ marginTop: 16 }}>
      <div className="divider-label">RISK SCORE OVER TIME</div>
      <div style={{ width: "100%", height: 160 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis dataKey="date" tick={{ fontFamily: "'Courier New', monospace", fontSize: 10, fill: "#888" }} />
            <YAxis domain={[0, 100]} tick={{ fontFamily: "'Courier New', monospace", fontSize: 10, fill: "#888" }} />
            <ReferenceLine y={40} stroke="#888" strokeDasharray="4 4" />
            <ReferenceLine y={70} stroke="#c0392b" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="score" stroke="#111" dot={{ fill: "#111", r: 2 }} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

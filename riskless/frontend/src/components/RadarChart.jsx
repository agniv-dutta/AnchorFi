import { PolarAngleAxis, PolarGrid, Radar, RadarChart as RChart, ResponsiveContainer } from "recharts";

function styleForScore(score) {
  if (score >= 70) return { stroke: "#c0392b", fill: "rgba(192,57,43,0.2)" };
  if (score >= 40) return { stroke: "#888", fill: "rgba(136,136,136,0.2)" };
  return { stroke: "#111", fill: "rgba(17,17,17,0.1)" };
}

export default function RiskRadarChart({ assessResult }) {
  const data = [
    { subject: "Code", score: assessResult.code_risk.score },
    { subject: "Liquidity", score: assessResult.liquidity_risk.score },
    { subject: "Team", score: assessResult.team_risk.score },
    { subject: "Track Record", score: assessResult.track_record.score },
  ];
  const style = styleForScore(assessResult.composite_risk_score);

  return (
    <div style={{ marginTop: 16 }}>
      <div className="k-label" style={{ fontSize: 10, marginBottom: 8 }}>RISK PROFILE</div>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <RChart data={data} outerRadius={92}>
            <PolarGrid stroke="#ddd9d0" />
            <PolarAngleAxis dataKey="subject" tick={{ fontFamily: "'Courier New', monospace", fontSize: 10, fill: "#888" }} />
            <Radar dataKey="score" stroke={style.stroke} fill={style.fill} fillOpacity={1} />
          </RChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

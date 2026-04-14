function riskClass(score) {
  if (score >= 70) return "risk-high";
  if (score >= 40) return "risk-medium";
  return "risk-low";
}

function riskLabel(score) {
  if (score >= 70) return "HIGH RISK";
  if (score >= 40) return "MEDIUM RISK";
  return "LOW RISK";
}

export default function RiskGauge({ target, score, premium, coverageDays, animatedScore }) {
  const size = 160;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const progress = Math.max(0, Math.min(100, score));
  const circumference = Math.PI * radius;
  const filled = (progress / 100) * circumference;

  const color = progress < 40 ? "#2d7a4f" : progress < 70 ? "#888888" : "#c0392b";

  const startX = strokeWidth / 2;
  const endX = size - strokeWidth / 2;

  return (
    <div>
      <div className="k-mono" style={{ fontSize: 11, fontWeight: 700, letterSpacing: 4, textTransform: "uppercase", color: "#888", marginBottom: 8 }}>{target}</div>
      <div className="k-mono" style={{ fontSize: 96, fontWeight: 900, lineHeight: 0.9, letterSpacing: -4, color: "#111" }}>
        {animatedScore}<span style={{ fontSize: 24, color: "#888", fontWeight: 400 }}>/100</span>
      </div>
      <span className={`risk-badge ${riskClass(score)}`}>{riskLabel(score)}</span>
      <div className="k-mono" style={{ marginTop: 10, fontSize: 12 }}>EST. PREMIUM: ${premium} USDC / {coverageDays} DAYS</div>
      <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`} style={{ marginTop: 12 }}>
        <path
          d={`M ${startX} ${cy} A ${radius} ${radius} 0 0 1 ${endX} ${cy}`}
          fill="none"
          stroke="#ddd9d0"
          strokeWidth={strokeWidth}
          strokeLinecap="butt"
        />
        <path
          d={`M ${startX} ${cy} A ${radius} ${radius} 0 0 1 ${endX} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="butt"
          strokeDasharray={`${filled} ${circumference}`}
        />
        {[40, 70].map((threshold) => {
          const angle = Math.PI - (threshold / 100) * Math.PI;
          const tx = cx + radius * Math.cos(angle);
          const ty = cy - radius * Math.sin(angle);
          return <circle key={threshold} cx={tx} cy={ty} r={3} fill={threshold === 40 ? "#888" : "#c0392b"} />;
        })}
      </svg>
    </div>
  );
}


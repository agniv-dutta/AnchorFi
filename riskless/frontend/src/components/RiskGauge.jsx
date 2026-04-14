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
  const radius = 76;
  const circumference = Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score));
  const stroke = progress >= 70 ? "#c0392b" : progress >= 40 ? "#888" : "#2d7a4f";
  const dash = (progress / 100) * circumference;

  return (
    <div>
      <div className="k-mono" style={{ fontSize: 13, color: "#888", textTransform: "uppercase" }}>{target}</div>
      <div className="k-mono" style={{ fontSize: 80, fontWeight: 900, lineHeight: 1 }}>
        {animatedScore}<span style={{ fontSize: 24, color: "#888", fontWeight: 400 }}>/100</span>
      </div>
      <span className={`risk-badge ${riskClass(score)}`}>{riskLabel(score)}</span>
      <div className="k-mono" style={{ marginTop: 10, fontSize: 12 }}>EST. PREMIUM: ${premium} USDC / {coverageDays} DAYS</div>
      <svg width="200" height="120" viewBox="0 0 200 120" style={{ marginTop: 12 }}>
        <path d="M 20 100 A 80 80 0 0 1 180 100" stroke="#ddd9d0" strokeWidth="12" fill="none" />
        <path d="M 20 100 A 80 80 0 0 1 180 100" stroke={stroke} strokeWidth="12" fill="none" strokeDasharray={`${dash} ${circumference}`} />
      </svg>
    </div>
  );
}


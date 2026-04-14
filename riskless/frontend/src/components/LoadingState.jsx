export default function LoadingState({ step }) {
  return (
    <div className="card" style={{ minHeight: 120, display: "flex", flexDirection: "column", justifyContent: "center", gap: 8 }}>
      <div className="k-mono" style={{ fontSize: 13 }}>{step >= 0 ? "> FETCHING ON-CHAIN DATA..." : ""}</div>
      <div className="k-mono" style={{ fontSize: 13 }}>{step >= 1 ? "> RUNNING AI ANALYSIS..." : ""}</div>
      <div className="k-mono" style={{ fontSize: 13 }}>{step >= 2 ? "> CALCULATING PREMIUM..." : ""}</div>
      {step >= 3 ? <div className="k-mono" style={{ animation: "blink .8s infinite" }}>▊</div> : null}
      <style>{"@keyframes blink {0%,100%{opacity:1}50%{opacity:0}}"}</style>
    </div>
  );
}

export default function Ticker() {
  return (
    <div style={{ width: "100%", background: "#111", color: "#f5f0e8", height: "32px", overflow: "hidden", display: "flex", alignItems: "center" }}>
      <div style={{ whiteSpace: "nowrap", animation: "marquee 25s linear infinite", fontSize: "10px", fontFamily: "'Courier New', monospace", letterSpacing: "2px", textTransform: "uppercase" }}>
        ETHEREUM MAINNET · POWERED BY GOPLUS + DEFILLAMA + AI · DATA REFRESHED DAILY · NOT FINANCIAL ADVICE · HACKATHON DEMO · ETHEREUM MAINNET · POWERED BY GOPLUS + DEFILLAMA + AI · DATA REFRESHED DAILY · NOT FINANCIAL ADVICE · HACKATHON DEMO ·
      </div>
      <style>{"@keyframes marquee {0%{transform:translateX(0)}100%{transform:translateX(-50%)}}"}</style>
    </div>
  );
}

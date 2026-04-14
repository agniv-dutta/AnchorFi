export default function Nav() {
  return (
    <nav style={{ borderBottom: "3px solid #111", padding: "16px 40px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div style={{ fontFamily: "Georgia, serif", fontSize: "22px", fontWeight: 900, letterSpacing: "-1px", textTransform: "uppercase" }}>ANCHORFI</div>
      <div style={{ border: "2px solid #111", padding: "4px 12px", fontFamily: "'Courier New', monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase" }}>ETHEREUM MAINNET ONLY (V1)</div>
    </nav>
  );
}

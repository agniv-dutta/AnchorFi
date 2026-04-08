export default function PremiumEstimate({ coverageAmount, coverageDays, premium }) {
  const amt = Number(coverageAmount);
  const days = Number(coverageDays);
  return (
    <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
      <div className="text-xs uppercase tracking-widest text-slate-400">
        Premium estimate
      </div>
      <div className="mt-2 text-sm text-slate-200">
        Insure <span className="font-semibold">{amt.toLocaleString()}</span> USDC for{" "}
        <span className="font-semibold">{days}</span> days ={" "}
        <span className="font-semibold">{Number(premium).toLocaleString()}</span> USDC
      </div>
      <div className="mt-2 text-xs text-slate-400">
        Disclaimer: This is an illustrative estimate based on risk signals, not a binding quote.
      </div>
    </div>
  );
}


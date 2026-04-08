function CategoryCard({ title, category }) {
  const score = category?.score ?? 0;
  const flags = category?.flags ?? [];
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">{title}</div>
        <div className="text-sm text-slate-200">{score}/100</div>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-2 rounded-full bg-indigo-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <ul className="mt-4 space-y-1 text-sm text-slate-300">
        {flags.slice(0, 4).map((f) => (
          <li key={f} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-slate-500" />
            <span>{f}</span>
          </li>
        ))}
        {flags.length === 0 ? <li className="text-slate-500">No flags</li> : null}
      </ul>
    </div>
  );
}

export default function RiskBreakdown({ result }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <CategoryCard title="Code Risk" category={result.code_risk} />
      <CategoryCard title="Liquidity Risk" category={result.liquidity_risk} />
      <CategoryCard title="Team Risk" category={result.team_risk} />
      <CategoryCard title="Track Record" category={result.track_record} />
    </div>
  );
}


import { useEffect, useState } from "react";

function formatTs(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function AssessmentHistory({ apiBase }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${apiBase}/history?limit=10`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) setItems(data.items || []);
      } catch (e) {
        if (!cancelled) setError(e?.message || "Failed to load history");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">Recent assessments</div>
        <div className="text-xs text-slate-400">Cached daily</div>
      </div>
      {error ? (
        <div className="mt-3 text-sm text-rose-200">{error}</div>
      ) : null}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-widest text-slate-500">
            <tr>
              <th className="py-2">Target</th>
              <th className="py-2">Score</th>
              <th className="py-2">Premium</th>
              <th className="py-2">As of</th>
            </tr>
          </thead>
          <tbody className="text-slate-200">
            {items.length ? (
              items.map((it) => (
                <tr key={it.id} className="border-t border-slate-800">
                  <td className="py-3 pr-4 font-mono text-xs">{it.target}</td>
                  <td className="py-3">{it.composite_risk_score}</td>
                  <td className="py-3">{it.premium_usdc}</td>
                  <td className="py-3 text-xs text-slate-400">
                    {formatTs(it.as_of)}
                  </td>
                </tr>
              ))
            ) : (
              <tr className="border-t border-slate-800">
                <td className="py-4 text-slate-500" colSpan={4}>
                  No history yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


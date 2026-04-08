export default function AddressInput({ value, onChange }) {
  return (
    <div>
      <label className="text-xs text-slate-400">
        Contract address or protocol name
      </label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g. 0x… or AAVE"
        className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-base outline-none focus:border-slate-600"
      />
    </div>
  );
}


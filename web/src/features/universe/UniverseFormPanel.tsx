type UniverseFormPanelProps = {
  selectedId: number;
  tickerError?: string;
  tickerSuccess?: string;
  universeError?: string;
  universeSuccess?: string;
  createAction: (formData: FormData) => void | Promise<void>;
  updateAction: (formData: FormData) => void | Promise<void>;
  addTickerAction: (formData: FormData) => void | Promise<void>;
};

const inputClass = "flex h-9 rounded-md border border-zinc-200 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-zinc-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-950";
const btnPrimary = "inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-50 shadow hover:bg-zinc-700 transition-colors";
const btnOutline = "inline-flex items-center justify-center rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium shadow-sm hover:bg-zinc-100 transition-colors";

export function UniverseFormPanel({
  selectedId,
  tickerError,
  tickerSuccess,
  universeError,
  universeSuccess,
  createAction,
  updateAction,
  addTickerAction,
}: UniverseFormPanelProps) {
  return (
    <section className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6 space-y-4 text-sm">
      <div className="font-semibold tracking-tight text-zinc-900">Universe Management</div>
      {universeSuccess && <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-green-700">{universeSuccess}</p>}
      {universeError && <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-700">{universeError}</p>}
      <form action={createAction} className="flex gap-2 flex-wrap items-center">
        <input name="name" placeholder="New universe name" className={inputClass} />
        <input name="description" placeholder="Description (optional)" className={inputClass} />
        <button type="submit" className={btnPrimary}>Create Universe</button>
      </form>
      {selectedId ? (
        <form action={updateAction} className="flex gap-2 flex-wrap items-center">
          <input type="hidden" name="universe_id" value={selectedId} />
          <input name="name" placeholder="Rename selected universe" className={inputClass} />
          <input name="description" placeholder="Update description" className={inputClass} />
          <button type="submit" className={btnOutline}>Update Universe</button>
        </form>
      ) : null}
      {selectedId ? (
        <form action={addTickerAction} className="flex gap-2 flex-wrap items-center">
          <input type="hidden" name="universe_id" value={selectedId} />
          <input name="ticker" placeholder="Add ticker (e.g. AAPL)" className={inputClass} />
          <button type="submit" className={btnOutline}>Add Ticker</button>
        </form>
      ) : null}
      {tickerSuccess && <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-green-700">{tickerSuccess}</p>}
      {tickerError && <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-700">{tickerError}</p>}
    </section>
  );
}

type UniverseFormPanelProps = {
  selectedId: number;
  tickerError?: string;
  createAction: (formData: FormData) => void | Promise<void>;
  updateAction: (formData: FormData) => void | Promise<void>;
  addTickerAction: (formData: FormData) => void | Promise<void>;
};

export function UniverseFormPanel({
  selectedId,
  tickerError,
  createAction,
  updateAction,
  addTickerAction,
}: UniverseFormPanelProps) {
  return (
    <section className="rounded border p-3 space-y-3 text-sm">
      <div className="font-semibold">Universe Management</div>
      <form action={createAction} className="flex gap-2 flex-wrap items-center">
        <input name="name" placeholder="New universe name" className="rounded border px-2 py-1" />
        <input name="description" placeholder="Description (optional)" className="rounded border px-2 py-1" />
        <button type="submit" className="rounded border px-3 py-1">Create Universe</button>
      </form>
      {selectedId ? <form action={updateAction} className="flex gap-2 flex-wrap items-center"><input type="hidden" name="universe_id" value={selectedId} /><input name="name" placeholder="Rename selected universe" className="rounded border px-2 py-1" /><input name="description" placeholder="Update description" className="rounded border px-2 py-1" /><button type="submit" className="rounded border px-3 py-1">Update Universe</button></form> : null}
      {selectedId ? <form action={addTickerAction} className="flex gap-2 flex-wrap items-center"><input type="hidden" name="universe_id" value={selectedId} /><input name="ticker" placeholder="Add ticker (e.g. AAPL)" className="rounded border px-2 py-1" /><button type="submit" className="rounded border px-3 py-1">Add Ticker</button></form> : null}
      {tickerError ? <p className="rounded border border-red-300 bg-red-50 p-2 text-red-700">{tickerError}</p> : null}
    </section>
  );
}

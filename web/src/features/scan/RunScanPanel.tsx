import type { Template, UniverseScanResponse } from "@/lib/api";

type RunScanPanelProps = {
  selectedId: number;
  templates: Template[];
  scanResult: UniverseScanResponse | null;
  action: (formData: FormData) => void | Promise<void>;
};

const selectClass = "flex h-9 rounded-md border border-zinc-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-950";
const btnPrimary = "inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-50 shadow hover:bg-zinc-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

export function RunScanPanel({ selectedId, templates, scanResult, action }: RunScanPanelProps) {
  const hasTemplates = templates.length > 0;
  return (
    <section className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6 space-y-4 text-sm">
      <div className="font-semibold tracking-tight text-zinc-900">Run Scan</div>
      <form action={action} className="flex gap-2 items-center flex-wrap">
        <input type="hidden" name="universe_id" value={selectedId || ""} />
        <select name="template_id" className={selectClass} defaultValue={templates[0]?.id ?? ""} disabled={!hasTemplates}>
          {templates.map((t) => <option key={t.id} value={t.id}>{t.name} v{t.version}</option>)}
        </select>
        <button type="submit" className={btnPrimary} disabled={!hasTemplates}>Run Candidates</button>
      </form>
      {!hasTemplates && <p className="text-zinc-500">No strategy templates found.</p>}
      {scanResult && (
        <div className="rounded-md border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs text-zinc-600 space-x-4">
          <span>✓ {scanResult.tickers_processed} tickers</span>
          <span>{scanResult.ohlcv_rows_written} OHLCV rows</span>
          <span>{scanResult.candidates_created} candidates</span>
          {scanResult.error_count > 0 && <span className="text-red-600">{scanResult.error_count} errors</span>}
        </div>
      )}
    </section>
  );
}

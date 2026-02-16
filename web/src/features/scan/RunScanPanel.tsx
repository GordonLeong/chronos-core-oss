import type { Template, UniverseScanResponse } from "@/lib/api";

type RunScanPanelProps = {
  selectedId: number;
  templates: Template[];
  scanResult: UniverseScanResponse | null;
  action: (formData: FormData) => void | Promise<void>;
};

export function RunScanPanel({ selectedId, templates, scanResult, action }: RunScanPanelProps) {
  const hasTemplates = templates.length > 0;
  return (
    <section className="rounded border p-3 space-y-3 text-sm">
      <div className="font-semibold">Run Scan</div>
      <form action={action} className="flex gap-2 items-center">
        <input type="hidden" name="universe_id" value={selectedId || ""} />
        <select name="template_id" className="rounded border px-2 py-1" defaultValue={templates[0]?.id ?? ""} disabled={!hasTemplates}>
          {templates.map((t) => <option key={t.id} value={t.id}>{t.name} v{t.version}</option>)}
        </select>
        <button type="submit" className="rounded border px-3 py-1" disabled={!hasTemplates}>Run Candidates</button>
      </form>
      {!hasTemplates ? <p className="text-zinc-600">No strategy templates found.</p> : null}
      {scanResult ? <div className="text-xs">processed {scanResult.tickers_processed}, ohlcv {scanResult.ohlcv_rows_written}, candidates {scanResult.candidates_created}, errors {scanResult.error_count}</div> : null}
    </section>
  );
}
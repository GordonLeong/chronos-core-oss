
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
  listUniverses,
  listUniverseStocks,
  getUniverseOHLCV,
  getUniverseSignals,
  listTemplates,
  listUniverseCandidates,
  createUniverse,
  updateUniverse,
  addTickerToUniverse,
  OHLCVPoint,
  runUniverseScan,
  UniverseScanResponse,
} from "@/lib/api";
import { UniversePanel } from "@/features/universe/UniversePanel";
import { UniverseFormPanel } from "@/features/universe/UniverseFormPanel";
import { TemplatePanel} from "@/features/template/TemplatePanel";
import { RunScanPanel } from "@/features/scan/RunScanPanel";
import { CandidatesPanel } from "@/features/candidates/CandidatesPanel";
import { parseTemplateConfig, type TemplateConfig } from "@/features/template/config";

async function runCandidates(formData: FormData){
  "use server";
  // FormData values are string-like; convert explicitly before validation.
  const universe_id = Number(formData.get("universe_id"));
  const template_id = Number(formData.get("template_id"));
  if(!Number.isFinite(universe_id) || !Number.isFinite(template_id)) return;
  const result = await runUniverseScan(universe_id,{
    template_id,
    provider: "yahooquery",
    interval: "1d"
  });
  const encoded = encodeURIComponent(JSON.stringify(result));
  revalidatePath("/")
  redirect(`/?universe=${universe_id}&scan=${encoded}`)
}

async function createUniverseAction(formData: FormData) {
  "use server";
  const name = String(formData.get("name") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim() || null;
  if (!name) return;
  await createUniverse({ name, description });
  revalidatePath("/");
}

async function updateUniverseAction(formData: FormData) {
  "use server";
  const universeId = Number(formData.get("universe_id"));
  const name = String(formData.get("name") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim() || null;
  if (!Number.isFinite(universeId)) return;
  // PATCH payload is partial: only include fields the user actually intended to change.
  const payload: { name?: string; description?: string | null} = {};
  if (name) payload.name = name;
  if (formData.has("description")) payload.description = description;
  if(Object.keys(payload).length === 0) return;
  await updateUniverse(universeId, payload);
  revalidatePath("/");
}

async function addTickerAction(formData: FormData) {
  "use server";
  const universeId = Number(formData.get("universe_id"));
  const ticker = String(formData.get("ticker") ?? "").trim();
  if (!Number.isFinite(universeId) || !ticker) return;
  try {
    await addTickerToUniverse(universeId, ticker);
  } catch (err) {
    // Bubble backend validation error into URL so the server component can render feedback.
    const message = err instanceof Error ? err.message : "failed to add ticker";
    redirect(`/?universe=${universeId}&ticker_error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/");
  redirect(`/?universe=${universeId}`);
}




export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ universe?: string; ticker_error?: string; scan?: string }>;
}){
  const { universe, ticker_error, scan } = await searchParams;
  const universes = await listUniverses();
  const templates = await listTemplates("strategy");
  
  const selectedTemplate = templates[0] ?? null;

  const selectedTemplateConfig: TemplateConfig | null = selectedTemplate
    ? parseTemplateConfig(selectedTemplate.config_json)
    : null;
  // Default to first available universe when query param is absent.
  const selectedId = Number(universe ?? universes[0]?.id ?? 0);
  let scanResult: UniverseScanResponse | null = null;
  if (scan) {
    try{
      scanResult = JSON.parse(scan) as UniverseScanResponse;
    }catch{
      scanResult=null;
    }
  }
  // Fetch independent datasets in parallel for faster SSR.
  const [stocks, ohlcv, signals, candidates] = selectedId
    ? await Promise.all([
        listUniverseStocks(selectedId),
        getUniverseOHLCV(selectedId, 30),
        getUniverseSignals(selectedId, 30),
        listUniverseCandidates(selectedId),
      ])
    : [[], { data: {} }, { data: {} }, []];
  


  const ohlcvData = ohlcv.data as Record<string, OHLCVPoint[]>;
  const ohlcvTickers = Object.keys(ohlcvData);
  const activeTicker = ohlcvTickers[0] ?? "";
  const activeCandles: OHLCVPoint[] = activeTicker ? ohlcvData[activeTicker] ?? [] : [];

   return (
     <main className="mx-auto max-w-5xl p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Chronos</h1>

      <UniversePanel universes={universes} selectedId={selectedId}/>
      <UniverseFormPanel
        selectedId={selectedId}
        tickerError={ticker_error}
        createAction={createUniverseAction}
        updateAction={updateUniverseAction}
        addTickerAction={addTickerAction}     
      />


      <TemplatePanel
      selectedTemplate={selectedTemplate}
      selectedTemplateConfig={selectedTemplateConfig}
      />
      <RunScanPanel
      selectedId={selectedId}
      templates={templates}
      scanResult={scanResult}
      action={runCandidates}
      />
      <section className="rounded border p-3 text-xs space-y-2">
        <div className="font-semibold">Market Data (Debug)</div>
        <div>stocks: {stocks.length ? stocks.join(", ") : "-"}</div>
        <div>signal keys: {Object.keys(signals.data).join(", ") || "-"}</div>
        <div>candles: {activeTicker || "none"}</div>
        <table className="w-full text-left">
          <thead>
            <tr>
              <th>date</th><th>open</th><th>high</th><th>low</th><th>close</th><th>volume</th>
            </tr>
          </thead>
          <tbody>
            {activeCandles.map((c) => (
              <tr key={c.date}>
                <td>{c.date}</td><td>{c.open}</td><td>{c.high}</td>
                <td>{c.low}</td><td>{c.close}</td><td>{c.volume ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <CandidatesPanel candidates={candidates} />
     

      

     </main>
   );
}
          

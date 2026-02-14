
import Link from "next/link";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
  listUniverses,
  listUniverseStocks,
  getUniverseOHLCV,
  getUniverseSignals,
  listTemplates,
  generateCandidates,
  listUniverseCandidates,
  createUniverse,
  updateUniverse,
  addTickerToUniverse,

  
} from "@/lib/api";

async function runCandidates(formData: FormData){
  "use server";
  // FormData values are string-like; convert explicitly before validation.
  const universe_id = Number(formData.get("universe_id"));
  const template_id = Number(formData.get("template_id"));
  if(!Number.isFinite(universe_id) || !Number.isFinite(template_id)) return;
  await generateCandidates({ universe_id, template_id, provider: "yahooquery", interval: "1d"});
  // Invalidate the route cache so the next render includes fresh candidates.
  revalidatePath("/")

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
  searchParams: Promise<{ universe?: string; ticker_error?: string }>;
}){
  const { universe, ticker_error } = await searchParams;
  const universes = await listUniverses();
  const templates = await listTemplates("strategy");
  const hasTemplates = templates.length > 0;
  // Default to first available universe when query param is absent.
  const selectedId = Number(universe ?? universes[0]?.id ?? 0);
  
  // Fetch independent datasets in parallel for faster SSR.
  const [stocks, ohlcv, signals, candidates] = selectedId
   ? await Promise.all([
      listUniverseStocks(Number(selectedId)),
      getUniverseOHLCV(Number(selectedId),30),
      getUniverseSignals(Number(selectedId),30),
      listUniverseCandidates(selectedId),
     ])
    : [[], { data: {} }, { data: {} }, []];

   return (
     <main className="mx-auto max-w-5xl p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Chronos</h1>

      <div className="flex gap-2 flex-wrap">
        {universes.map((u) => (
          <Link key={u.id} href={`/?universe=${u.id}`} className={`rounded border px-3 py-1 ${selectedId === u.id ? "bg-zinc-900 text-white" : ""}`}>
            {u.name}
          </Link>
        ))}
      </div>

      <div className="rounded border p-3 space-y-3">
      <form action={createUniverseAction} className="flex gap-2 flex-wrap items-center">
        <input name="name" placeholder="New universe name" className="rounded border px-2 py-1" />
        <input name="description" placeholder="Description (optional)" className="rounded border px-2 py-1" />
        <button type="submit" className="rounded border px-3 py-1">Create Universe</button>
      </form>

      {selectedId ? (
        <form action={updateUniverseAction} className="flex gap-2 flex-wrap items-center">
          <input type="hidden" name="universe_id" value={selectedId} />
          <input name="name" placeholder="Rename selected universe" className="rounded border px-2 py-1" />
          <input name="description" placeholder="Update description" className="rounded border px-2 py-1" />
          <button type="submit" className="rounded border px-3 py-1">Update Universe</button>
        </form>
      ) : null}

      {selectedId ? (
        <form action={addTickerAction} className="flex gap-2 flex-wrap items-center">
          <input type="hidden" name="universe_id" value={selectedId} />
          <input name="ticker" placeholder="Add ticker (e.g. AAPL)" className="rounded border px-2 py-1" />
          <button type="submit" className="rounded border px-3 py-1">Add Ticker</button>
        </form>
      ) : null}
    </div>

      {ticker_error ? (
        <p className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-700">
          {ticker_error}
        </p>
      ) : null}

      <form action={runCandidates} className="flex gap-2 items-center">
        <input type="hidden" name="universe_id" value={selectedId || ""} />
        <select
          name="template_id"
          className="rounded border px-2 py-1"
          defaultValue={templates[0]?.id ?? ""}
          disabled={!hasTemplates}
        >
          {templates.map((t) => (
            <option key={t.id} value={t.id}>{t.name} v{t.version}</option>
          ))}
        </select>
        <button type="submit" className="rounded border px-3 py-1" disabled={!hasTemplates}>
          Run Candidates
        </button>
      </form>
      {!hasTemplates ? <p className="text-sm text-zinc-600">No strategy templates found.</p> : null}
        <pre className="rounded border p-3 text-xs overflow-auto">stocks: {JSON.stringify(stocks, null, 2)}</pre>
        <pre className="rounded border p-3 text-xs overflow-auto">ohlcv keys: {JSON.stringify(Object.keys(ohlcv.data), null, 2)}</pre>
        <pre className="rounded border p-3 text-xs overflow-auto">signal keys: {JSON.stringify(Object.keys(signals.data), null, 2)}</pre>
        <pre className="rounded border p-3 text-xs overflow-auto">candidates: {JSON.stringify(candidates, null, 2)}</pre>

     </main>
   );
}
          

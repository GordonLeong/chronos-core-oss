
type Universe = { id: number; name: string; description: string | null };
type OHLCVPoint = {
  date:string; open: number; high:number; low: number; close: number; volume: number | null;
};

type SignalPoint = {
  as_of: string; rsi: number | null; macd: number | null; macd_signal: number | null;
  ema_20: number | null; ema_50: number | null; bb_upper: number | null; bb_lower: number | null;
};
type UniverseOHLCVResponse = {
  universe_id: number; provider: string; interval: string; data: Record<string, OHLCVPoint[]>;
};
type UniverseSignalsResponse = {
  universe_id: number; provider: string; interval: string; data: Record<string, SignalPoint[]>;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";


async function getJSON<T>(path: string): Promise<T> { 
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store"});
  if (!res.ok) throw new Error(`Request failed: ${res.status} :${path}`);
  return res.json();
}

export default async function Home({ searchParams }: { searchParams: Promise<{ universe?: string }> }){
  const {universe} = await searchParams;
  const universes = await getJSON<Universe[]>("http://127.0.0.1:8000/universes");
  const selectedId = universe ?? universes[0]?.id?.toString();
  // const base = "http://127.0.0.1:8000";
  const [stocks, ohlcv, signals] = selectedId
   ? await Promise.all([
       getJSON<string[]>(`/universes/${selectedId}/stocks`),
       getJSON<UniverseOHLCVResponse>(`/universes/${selectedId}/ohlcv?limit=30`),
       getJSON<UniverseSignalsResponse>(`/universes/${selectedId}/signals?limit=30`),
     ])
    :[[], { data: {} } as UniverseOHLCVResponse, { data: {} } as UniverseSignalsResponse];


   return (
    <main className="mx-auto max-w-5xl p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Chronos</h1>
      <div className="flex gap-2 flex-wrap">{universes.map((u) => <a key={u.id} href={`/?universe=${u.id}`} className={`rounded border px-3 py-1 ${selectedId === String(u.id) ?  "bg-zinc-900 text-white" : ""}`}>{u.name}</a>)}</div>
      <pre className="rounded border p-3 text-xs overflow-auto">stocks: {JSON.stringify(stocks, null,2)}</pre>
      <pre className="rounded border p-3 text-xs overflow-auto">ohlcv keys: {JSON.stringify(Object.keys(ohlcv.data), null,2)}</pre>
      <pre className="rounded border p-3 text-xs overflow-auto">signal keys: {JSON.stringify(Object.keys(signals.data),null,2)}</pre>
    </main>
   );

}
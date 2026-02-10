
type Universe = { id: number; name: string; description: string | null };


async function getJSON<T>(url: string): Promise<T> { 
  const res = await fetch(url, { cache: "no-store"});
  if (!res.ok) throw new Error(`Request failed: ${res.status} :${url}`);
  return res.json();
}

export default async function Home({ searchParams }: { searchParams: Promise<{ universe?: string }> }){
  const {universe} = await searchParams;
  const universes = await getJSON<Universe[]>("http://127.0.0.1:8000/universes");
  const selectedId = universe ?? universes[0]?.id?.toString();
  const base = "http://127.0.0.1:8000";
  const [stocks, ohlcv, signals] = selectedId
   ? await Promise.all([
    getJSON<string[]>(`${base}/universes/${selectedId}/stocks`),
    getJSON<{ data: Record<string, unknown[]> }>(`${base}/universes/${selectedId}/ohlcv?limit=30`),
    getJSON<{ data: Record<string, unknown[]> }>(`${base}/universes/${selectedId}/signals?limit=30`),
   ])
   : [[],{ data: {} }, { data: {} }];

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
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type TemplateKind = "strategy" | "trade" | "risk";

export type Template ={
    id: number;
    kind: TemplateKind;
    name: string;
    version: number;
    description: string | null;
    config_json: string;
    created_at: string | null;
}
export type Candidate = {
  id: number;
  universe_id: number;
  template_id: number;
  ticker: string;
  as_of: string;
  score: number;
  status: "proposed" | "selected" | "rejected";
  reason_code: string | null;
  payload_json: string;
};

export type GenerateCandidatesRequest = {
  universe_id: number;
  template_id: number;
  provider?: string;
  interval?: string;
};

export type Universe = { id: number; name: string; description: string | null };
type OHLCVPoint = {
  date:string; open: number; high:number; low: number; close: number; volume: number | null;
};

export type SignalPoint = {
  as_of: string; rsi: number | null; macd: number | null; macd_signal: number | null;
  ema_20: number | null; ema_50: number | null; bb_upper: number | null; bb_lower: number | null;
};

export type UniverseOHLCVResponse = {
  universe_id: number; provider: string; interval: string; data: Record<string, OHLCVPoint[]>;
};

export type UniverseSignalsResponse = {
  universe_id: number; provider: string; interval: string; data: Record<string, SignalPoint[]>;
};

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${path}`);
  return (await res.json()) as T;
}

export async function generateCandidates(payload: GenerateCandidatesRequest){
    const res = await fetch(`${API_BASE}/candidates/generate`,{
        method:"POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Generate failed: ${res.status}`);
    return res.json() as Promise<{ universe_id: number; template_id: number; created_count: number }>;

}


export async function listUniverseCandidates(universeId: number) {
    const res = await fetch(`${API_BASE}/universes/${universeId}/candidates`, { cache : "no-store"});
    if (!res.ok) throw new Error(`Candidates load failed: ${res.status}`);
    return res.json() as Promise<Candidate[]>;
}

export function listUniverses() {
  return getJSON<Universe[]>("/universes");
}

export function listUniverseStocks(universeId: number) {
  return getJSON<string[]>(`/universes/${universeId}/stocks`);
}

export function getUniverseOHLCV(universeId: number, limit = 30) {
  return getJSON<UniverseOHLCVResponse>(`/universes/${universeId}/ohlcv?limit=${limit}`);
}

export function getUniverseSignals(universeId: number, limit = 30) {
  return getJSON<UniverseSignalsResponse>(`/universes/${universeId}/signals?limit=${limit}`);
}

export function listTemplates(kind?: TemplateKind){
    const qs = kind ? `?kind=${kind}` : "";
    return getJSON<Template[]>(`/templates${qs}`);
}


export type UniverseCreateInput = {
    name: string;
    description?: string | null;
};

export type UniverseUpdateInput = {
    name?: string;
    description?: string | null;
};

export async function createUniverse(payload: UniverseCreateInput) {
    const res = await fetch(`${API_BASE}/universes`,{
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error (`Create universe failed: ${res.status}`);
    return res.json() as Promise<Universe>;
}

export async function updateUniverse(universeId: number, payload: UniverseUpdateInput) {
  const res = await fetch(`${API_BASE}/universes/${universeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Update universe failed: ${res.status}`);
  return res.json() as Promise<Universe>;
}

export async function addTickerToUniverse(universeId: number, ticker: string, name?: string) {
  const res = await fetch(`${API_BASE}/universes/${universeId}/stocks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, name }),
  });
  if (res.status === 422) {
    const body = await res.json().catch(() => ({ detail: "invalid ticker" }));
    throw new Error(String(body.detail ?? "invalid ticker"));
  }
  if (!res.ok) throw new Error(`Add ticker failed: ${res.status}`);
  return res.json() as Promise<{ universe_id: number; stock_id: number; ticker: string }>;
}
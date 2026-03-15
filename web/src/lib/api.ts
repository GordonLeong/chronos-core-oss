const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Template = {
  name: string;
  version: number;
  description: string | null;
  config_json: string;
  created_at: string | null;
}

export type TemplateUpdateInput = {
  name?: string;
  description?: string | null;
  config_json?: string;
}

/**
 * Contract: A Candidate represents a single stock that passed a Strategy Template at a specific time.
 * - status: Drives the "Deal Room" journal UI. Starts as "proposed".
 * - payload_json: Immutable snapshot of the indicators that triggered this candidate.
 */
export type Candidate = {
  id: number;
  template_id: number;
  ticker: string;
  as_of: string;
  score: number;
  status: "proposed" | "selected" | "rejected";
  reason_code: string | null;
  payload_json: string;
};





export type OHLCVPoint = {
  date: string; open: number; high: number; low: number; close: number; volume: number | null;
};

export type SignalPoint = {
  as_of: string; rsi: number | null; macd: number | null; macd_signal: number | null;
  ema_20: number | null; ema_50: number | null; bb_upper: number | null; bb_lower: number | null;
};





async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${path}`);
  return (await res.json()) as T;
}





export function listTemplates() {
  return getJSON<Template[]>("/templates");
}




export async function updateTemplate(templateId: number, payload: TemplateUpdateInput) {
  const res = await fetch(`${API_BASE}/templates/${templateId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Update template failed: ${res.status}`);
  return res.json() as Promise<Template>;
}
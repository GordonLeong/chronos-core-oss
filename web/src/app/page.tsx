
import {
  listUniverses,
  listTemplates,
  listUniverseCandidates,
  UniverseScanResponse,
} from "@/lib/api";

import {
  runCandidates,
  createUniverseAction,
  updateUniverseAction,
  addTickerAction,
} from "./actions";

import { UniversePanel } from "@/features/universe/UniversePanel";
import { UniverseFormPanel } from "@/features/universe/UniverseFormPanel";
import { TemplatePanel } from "@/features/template/TemplatePanel";
import { RunScanPanel } from "@/features/scan/RunScanPanel";
import { CandidatesPanel } from "@/features/candidates/CandidatesPanel";
import { parseTemplateConfig, type TemplateConfig } from "@/features/template/config";







export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{
    universe?: string;
    ticker_error?: string;
    ticker_success?: string;
    universe_error?: string;
    universe_success?: string;
    scan?: string
  }>;
}) {
  const { universe, ticker_error, ticker_success, universe_error, universe_success, scan } = await searchParams;
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
    try {
      scanResult = JSON.parse(scan) as UniverseScanResponse;
    } catch {
      scanResult = null;
    }
  }
  // Fetch independent datasets in parallel for faster SSR.
  const candidates = selectedId
    ? await listUniverseCandidates(selectedId)
    : [];



  return (
    <main className="mx-auto max-w-5xl p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Chronos</h1>

      <UniversePanel universes={universes} selectedId={selectedId} />
      <UniverseFormPanel
        selectedId={selectedId}
        tickerError={ticker_error}
        tickerSuccess={ticker_success}
        universeError={universe_error}
        universeSuccess={universe_success}
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

      <CandidatesPanel candidates={candidates} />




    </main>
  );
}


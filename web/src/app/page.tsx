
import {
  listTemplates,
} from "@/lib/api";

import {
  updateTemplateAction,
} from "./actions";

import { TemplatePanel } from "@/features/template/TemplatePanel";
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
    scan?: string;
    template_error?: string;
    template_success?: string;
  }>;
}) {
  const { template_error, template_success } = await searchParams;
  const templates = await listTemplates();
  const selectedTemplate = templates[0] ?? null;

  const selectedTemplateConfig: TemplateConfig | null = selectedTemplate
    ? parseTemplateConfig(selectedTemplate.config_json)
    : null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 space-y-5">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Chronos Manual Workbench</h1>
      
      <p className="text-zinc-500">
        [Phase 0] Pick a strategy template and underlying to start a manual evaluation run. 
        (Bot Studio and Universe Screening are now deprecated in favor of this decision-engine flow).
      </p>

      <div className="bg-zinc-50 border border-zinc-200 rounded-lg p-8 text-center text-zinc-400 italic">
        Manual Trade Workbench components (Evaluation Result, Choice, Approve) will be added here in Phase 0.
      </div>

      <TemplatePanel
        selectedTemplate={selectedTemplate}
        selectedTemplateConfig={selectedTemplateConfig}
        templateSuccess={template_success}
        templateError={template_error}
        updateAction={updateTemplateAction}
      />
    </main>
  );
}

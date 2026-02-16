import type { Template } from "@/lib/api";
import type { TemplateConfig } from "@/features/template/config";

export type TemplateConfig = {
  entry_rules?: unknown[];
  score_field?: string;
};

type TemplatePanelProps = {
  selectedTemplate: Template | null;
  selectedTemplateConfig: TemplateConfig | null;
};

export function TemplatePanel({
  selectedTemplate,
  selectedTemplateConfig,
}: TemplatePanelProps) {
  return (
    <section className="rounded border p-3 text-sm">
      <div className="mb-2 font-semibold">Template</div>
      {!selectedTemplate ? (
        <p className="text-zinc-600">No strategy templates available.</p>
      ) : (
        <>
          <div>name: {selectedTemplate.name} v{selectedTemplate.version}</div>
          <div>score_field: {selectedTemplateConfig?.score_field ?? "-"}</div>
          <pre className="mt-2 rounded border p-2 text-xs overflow-auto">
            {JSON.stringify(selectedTemplateConfig?.entry_rules ?? [], null, 2)}
          </pre>
        </>
      )}
    </section>
  );
}
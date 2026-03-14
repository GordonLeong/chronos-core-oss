"use client";

import { useState, useEffect } from "react";
import type { Template } from "@/lib/api";
import type { TemplateConfig, EntryRule, RuleOp } from "@/features/template/config";


type TemplatePanelProps = {
  selectedTemplate: Template | null;
  selectedTemplateConfig: TemplateConfig | null;
  templateSuccess?: string;
  templateError?: string;
  updateAction: (formData: FormData) => void | Promise<void>;

}


const OP_CHOICES: RuleOp[] = [">", ">=", "==", "<=", "<"];

export function TemplatePanel({
  selectedTemplate,
  selectedTemplateConfig,
  templateSuccess,
  templateError,
  updateAction,
}: TemplatePanelProps) {
  const [rules, setRules] = useState<EntryRule[]>([]);
  //Sync state when a new template is selected
  useEffect(() => {
    setRules(selectedTemplateConfig?.entry_rules ?? []);
  },
    [selectedTemplateConfig]);

  if (!selectedTemplate || !selectedTemplateConfig) {
    return (
      <section className="rounded border p-3 text-sm">
        <div className="mb-2 font-semibold">Template</div>
        <p className="text-zinc-600">No Strategy Templates available.</p>
      </section>
    );
  }

  //Helper to update a single rule

  const updateRule = (index: number, field: keyof EntryRule, value: string | number) => {
    const newRules = [...rules];
    newRules[index] = {
      ...newRules[index],
      [field]: value,
    };
    setRules(newRules);
  };

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };
  const addRule = () => {
    setRules([...rules, { field: "rsi", op: "<", value: 30 }]);
  };
  // Re-build the full config object to submit
  const finalConfig: TemplateConfig = {
    ...selectedTemplateConfig,
    entry_rules: rules,
  };
  return (
    <section className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6 space-y-4 text-sm">
      <div className="font-semibold tracking-tight text-zinc-900">
        Template: {selectedTemplate.name} <span className="text-zinc-500 font-normal">v{selectedTemplate.version}</span>
      </div>
      {templateSuccess && <p className="rounded border border-green-300 bg-green-50 p-2 text-green-700">{templateSuccess}</p>}
      {templateError && <p className="rounded border border-red-300 bg-red-50 p-2 text-red-700">{templateError}</p>}
      <form action={updateAction} className="space-y-3">
        <input type="hidden" name="template_id" value={selectedTemplate.id} />
        <input type="hidden" name="config_json" value={JSON.stringify(finalConfig)} />
        <div className="space-y-2">
          {rules.map((rule, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <input
                className="h-9 w-32 rounded-md border border-zinc-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-950"
                placeholder="Field (e.g. rsi)"
                value={rule.field}
                onChange={(e) => updateRule(idx, "field", e.target.value)}
              />
              <select
                className="h-9 rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-950"
                value={rule.op}
                onChange={(e) => updateRule(idx, "op", e.target.value as RuleOp)}
              >
                {OP_CHOICES.map((op) => (
                  <option key={op} value={op}>{op}</option>
                ))}
              </select>
              <input
                className="h-9 w-24 rounded-md border border-zinc-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-950"
                type="number"
                step="any"
                value={rule.value}
                onChange={(e) => updateRule(idx, "value", Number(e.target.value))}
              />
              <button
                type="button"
                className="rounded-md px-2 py-1 text-red-500 hover:text-red-700 hover:bg-red-50 transition-colors"
                onClick={() => removeRule(idx)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={addRule} className="inline-flex items-center justify-center rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium shadow-sm hover:bg-zinc-100 transition-colors">
            + Add Rule
          </button>
          <button type="submit" className="inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-50 shadow hover:bg-zinc-700 transition-colors">
            Save Template
          </button>
        </div>
      </form>
    </section>
  );
}



export type RuleOp = ">" | ">=" | "<" | "<=" | "==" | "!=";

export type EntryRule = {
    field: string;
    op: RuleOp;
    value: number;
};

export type TemplateConfig = {
    entry_rules: EntryRule[];
    score_field?: string;
}


export function parseTemplateConfig(raw: string): TemplateConfig | null {
  try {
    const parsed = JSON.parse(raw) as Partial<TemplateConfig>;
    if (!Array.isArray(parsed.entry_rules)) return null;
    return {
      entry_rules: parsed.entry_rules as EntryRule[],
      score_field: parsed.score_field,
    };
  } catch {
    return null;
  }
}
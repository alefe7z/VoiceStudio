/** Saved batch rules: named settings plus the output-name template, kept per device. */
export interface BatchRule {
  name: string;
  langs: string[];
  voice: string;
  preserve: boolean;
  template: string;
}

export const DEFAULT_TEMPLATE = '{name}_{lang}';
const STORAGE_KEY = 'voicestudio.batch.rules';
const MAX_RULES = 50;
// Windows rejects these in file names; the backend's portable_filename uses the same set.
const INVALID = /[<>:"/\\|?*\u0000-\u001f]/g;

export interface OutputNameInput {
  filename: string;
  lang: string;
  jobId: string;
  createdAt: number;
}

/** Expand `{name}`, `{lang}`, `{date}` and `{job}` into a portable `.mp4` file name. */
export function formatOutputName(template: string, input: OutputNameInput): string {
  const created = new Date(input.createdAt < 1e12 ? input.createdAt * 1000 : input.createdAt);
  const date = Number.isNaN(created.getTime()) ? '' : created.toISOString().slice(0, 10);
  const values: Record<string, string> = {
    name: input.filename.replace(/\.[^.]+$/, ''),
    lang: input.lang,
    date,
    job: input.jobId,
  };
  const expanded = (template.trim() || DEFAULT_TEMPLATE).replace(
    /\{(name|lang|date|job)\}/g,
    (_, key: string) => values[key] ?? '',
  );
  const safe = expanded
    .replace(INVALID, '_')
    .replace(/[. ]+$/, '')
    .trim();
  return (safe || values.name || 'output') + '.mp4';
}

function isRule(value: unknown): value is BatchRule {
  if (!value || typeof value !== 'object') return false;
  const rule = value as Record<string, unknown>;
  return (
    typeof rule.name === 'string' &&
    rule.name.trim() !== '' &&
    Array.isArray(rule.langs) &&
    rule.langs.every((lang) => typeof lang === 'string') &&
    typeof rule.voice === 'string' &&
    typeof rule.preserve === 'boolean' &&
    typeof rule.template === 'string'
  );
}

export function parseRules(raw: string | null): BatchRule[] {
  if (!raw) return [];
  try {
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter(isRule).slice(0, MAX_RULES) : [];
  } catch {
    return [];
  }
}

export function loadRules(): BatchRule[] {
  try {
    return parseRules(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return [];
  }
}

export function storeRules(rules: BatchRule[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(rules.slice(0, MAX_RULES)));
  } catch {
    // Storage blocked or full: the rules still apply for this session.
  }
}

/** Insert or replace by name (case-insensitive), newest first. */
export function upsertRule(rules: BatchRule[], rule: BatchRule): BatchRule[] {
  const name = rule.name.trim();
  const key = name.toLocaleLowerCase();
  return [
    { ...rule, name },
    ...rules.filter((item) => item.name.toLocaleLowerCase() !== key),
  ].slice(0, MAX_RULES);
}

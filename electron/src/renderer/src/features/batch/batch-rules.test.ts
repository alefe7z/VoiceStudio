import { expect, it } from 'vitest';
import { formatOutputName, parseRules, upsertRule, type BatchRule } from './batch-rules';

const input = { filename: 'Episode 1.mov', lang: 'es', jobId: 'abc123', createdAt: 1_760_000_000 };

it('expands every template token into a portable mp4 name', () => {
  expect(formatOutputName('{name}_{lang}', input)).toBe('Episode 1_es.mp4');
  expect(formatOutputName('{date}/{job}-{lang}', input)).toBe('2025-10-09_abc123-es.mp4');
  expect(formatOutputName('show: {name}?', input)).toBe('show_ Episode 1_.mp4');
  expect(formatOutputName('  ', input)).toBe('Episode 1_es.mp4');
  expect(formatOutputName('{unknown}...', input)).toBe('{unknown}.mp4');
  expect(formatOutputName('{lang}', { ...input, lang: '' })).toBe('Episode 1.mp4');
});

const rule = (name: string, extra: Partial<BatchRule> = {}): BatchRule => ({
  name,
  langs: ['Spanish'],
  voice: '',
  preserve: true,
  template: '{name}_{lang}',
  ...extra,
});

it('parses only well-formed rules and survives corrupt storage', () => {
  expect(parseRules(null)).toEqual([]);
  expect(parseRules('{nope')).toEqual([]);
  expect(parseRules(JSON.stringify({ name: 'x' }))).toEqual([]);
  const valid = rule('Podcast');
  expect(
    parseRules(JSON.stringify([valid, { ...valid, langs: 'es' }, { ...valid, name: ' ' }])),
  ).toEqual([valid]);
});

it('replaces a rule with the same name and keeps the newest first', () => {
  const rules = upsertRule(
    [rule('Podcast'), rule('Shorts')],
    rule(' podcast ', { preserve: false }),
  );
  expect(rules.map((item) => [item.name, item.preserve])).toEqual([
    ['podcast', false],
    ['Shorts', true],
  ]);
});

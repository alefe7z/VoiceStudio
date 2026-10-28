import type { HistoryItem } from '@/lib/api/types';

/** A take matches when its script, style or revision notes contain `needle` (lower-cased). */
export function matchesTakeSearch(item: HistoryItem, needle: string): boolean {
  return [item.text, item.instruct, item.notes].some((field) =>
    (field ?? '').toLocaleLowerCase().includes(needle),
  );
}

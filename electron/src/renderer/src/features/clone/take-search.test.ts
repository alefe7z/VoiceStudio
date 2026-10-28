import { expect, it } from 'vitest';
import type { HistoryItem } from '@/lib/api/types';
import { matchesTakeSearch } from './take-search';

const take = { text: 'Welcome to the Show', instruct: 'female, whisper', notes: 'Approved v2' };

it('searches the script, style and revision notes', () => {
  expect(matchesTakeSearch(take as HistoryItem, 'the show')).toBe(true);
  expect(matchesTakeSearch(take as HistoryItem, 'whisper')).toBe(true);
  expect(matchesTakeSearch(take as HistoryItem, 'approved')).toBe(true);
  expect(matchesTakeSearch(take as HistoryItem, 'trailer')).toBe(false);
  expect(matchesTakeSearch({ text: 'x', instruct: null } as HistoryItem, 'y')).toBe(false);
});

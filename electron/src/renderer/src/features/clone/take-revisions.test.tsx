import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { HistoryItem } from '@/lib/api/types';

const mock = vi.hoisted(() => ({
  history: [] as HistoryItem[],
  mutate: vi.fn(),
  openTake: vi.fn(),
}));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: 'en' } }),
}));
vi.mock('@/components/waveform-player', () => ({
  WaveformPlayer: ({ src }: { src: string }) => <div data-testid="player">{src}</div>,
}));
vi.mock('@/hooks/use-history', () => ({
  useHistory: () => ({ data: mock.history }),
  useSetHistoryNotes: () => ({ mutate: mock.mutate, isPending: false }),
}));
vi.mock('@/lib/api/client', () => ({ audioUrl: (path: string) => `/audio/${path}` }));
vi.mock('@/lib/store/takes', () => ({ openTake: mock.openTake }));

import { TakeRevisions, takeVersions } from './take-revisions';

const take = (id: string, text: string, created_at: number, extra: Partial<HistoryItem> = {}) =>
  ({ id, text, created_at, audio_path: `${id}.wav`, ...extra }) as HistoryItem;

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it('treats other takes of the same script as versions, newest first', () => {
  const item = take('a', 'Hello  world', 1);
  const history = [
    item,
    take('b', 'Hello world', 2),
    take('c', ' hello world', 3),
    take('d', 'Hello world', 4, { audio_path: '' }),
    take('e', 'Hello world ', 5),
  ];
  expect(takeVersions(item, history).map((v) => v.id)).toEqual(['e', 'b']);
});

it('saves trimmed notes and compares against a chosen version', () => {
  const item = take('a', 'Line', 1, { notes: 'first' });
  mock.history = [item, take('b', 'Line', 2, { notes: 'client pick' })];
  render(<TakeRevisions item={item} />);
  const save = screen.getByRole('button', { name: 'takeRevisions.notes_save' });
  expect(save).toBeDisabled();
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '  approved v2 ' } });
  fireEvent.click(save);
  expect(mock.mutate).toHaveBeenCalledWith(
    { id: 'a', notes: 'approved v2' },
    expect.objectContaining({ onSuccess: expect.any(Function) }),
  );
  mock.mutate.mock.calls[0][1].onSuccess({ id: 'a', notes: 'approved v2' });
  expect(mock.openTake).toHaveBeenCalledWith(
    expect.objectContaining({ id: 'a', notes: 'approved v2' }),
  );

  fireEvent.click(screen.getByRole('button', { pressed: false, name: /client pick/ }));
  expect(screen.getAllByTestId('player').map((p) => p.textContent)).toEqual([
    '/audio/a.wav',
    '/audio/b.wav',
  ]);
  fireEvent.click(screen.getByRole('button', { name: 'takeRevisions.open_version' }));
  expect(mock.openTake).toHaveBeenLastCalledWith(expect.objectContaining({ id: 'b' }));
});

import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { BatchJob } from '@shared/api/batch-types';

vi.mock('react-i18next', async (importOriginal) => ({
  ...(await importOriginal<typeof import('react-i18next')>()),
  useTranslation: () => ({ t: (key: string) => key, i18n: { resolvedLanguage: 'en' } }),
}));

import { BatchJobCard } from './batch-page';

afterEach(cleanup);

const job = (extra: Partial<BatchJob> = {}): BatchJob => ({
  id: 'j1',
  status: 'done',
  filename: 'episode.mp3',
  langs: ['es'],
  preserve_bg: true,
  created_at: 1,
  input_kind: 'audio',
  outputs: { es: '/data/batch/j1/output_es.m4a' },
  subtitles: { es: { srt: 's.srt', vtt: 's.vtt' } },
  transcript: { lang: 'en', srt: 't.srt' },
  ...extra,
});

function renderCard(value: BatchJob) {
  const handlers = {
    act: vi.fn(),
    recover: vi.fn(),
    download: vi.fn(),
    downloadSubtitles: vi.fn(),
    downloadPackage: vi.fn(),
  };
  render(
    <BatchJobCard job={value} acting={null} deleting={null} setDeleting={vi.fn()} {...handlers} />,
  );
  return handlers;
}

it('offers the output, subtitles, transcript and zip for a finished job', () => {
  const handlers = renderCard(job());
  fireEvent.click(screen.getByRole('button', { name: 'batchRules.subtitles_for' }));
  expect(handlers.downloadSubtitles).toHaveBeenCalledWith(
    expect.objectContaining({ id: 'j1' }),
    'es',
  );
  fireEvent.click(screen.getByRole('button', { name: /batchRules.transcript/ }));
  expect(handlers.downloadSubtitles).toHaveBeenLastCalledWith(
    expect.objectContaining({ id: 'j1' }),
    'original',
  );
  fireEvent.click(screen.getByRole('button', { name: /batchRules.download_all/ }));
  expect(handlers.downloadPackage).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole('button', { name: /dub.export es/ }));
  expect(handlers.download).toHaveBeenCalledWith(expect.objectContaining({ id: 'j1' }), 'es');
});

it('hides downloads until the job is done', () => {
  renderCard(job({ status: 'running', outputs: {}, subtitles: { es: { srt: 's.srt' } } }));
  expect(screen.queryByRole('button', { name: /batchRules/ })).toBeNull();
});

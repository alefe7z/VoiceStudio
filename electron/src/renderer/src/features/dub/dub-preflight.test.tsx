import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
const mock = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock('@/lib/api/client', () => ({
  apiJson: mock.api,
  describeError: (error: unknown) => String(error),
}));
vi.mock('react-i18next', async (importOriginal) => ({
  ...(await importOriginal<typeof import('react-i18next')>()),
  useTranslation: () => ({
    t: (key: string, values?: Record<string, unknown>) =>
      values ? `${key} ${JSON.stringify(values)}` : key,
  }),
}));
import { DubPreflight } from './dub-preflight';
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it('lists errors before warnings, reports the result and re-checks on demand', async () => {
  mock.api.mockResolvedValue({
    ready: false,
    counts: { error: 1, warning: 1, info: 0 },
    issues: [
      { code: 'empty_line', severity: 'warning', lang: 'es', segment: 2 },
      { code: 'track_audio_missing', severity: 'error', lang: 'es' },
    ],
  });
  const onReport = vi.fn();
  render(<DubPreflight jobId="job 1" revision="es:3" onReport={onReport} />);
  expect(mock.api).toHaveBeenCalledWith('/dub/preflight/job%201');
  await waitFor(() =>
    expect(onReport).toHaveBeenCalledWith(expect.objectContaining({ ready: false })),
  );
  const items = screen.getAllByRole('listitem').map((item) => item.textContent);
  expect(items[0]).toContain('dubPreflight.issue_track_audio_missing');
  expect(items[1]).toContain('"line":3');
  expect(screen.getByRole('status').textContent).toContain('dubPreflight.blocked');
  fireEvent.click(screen.getByRole('button', { name: 'dubPreflight.recheck' }));
  await waitFor(() => expect(mock.api).toHaveBeenCalledTimes(2));
});

it('clears the report when the check fails', async () => {
  mock.api.mockRejectedValue(new Error('offline'));
  const onReport = vi.fn();
  render(<DubPreflight jobId="job" revision="r" onReport={onReport} />);
  await waitFor(() => expect(onReport).toHaveBeenCalledWith(null));
  expect(screen.getByText('Error: offline')).toBeTruthy();
});

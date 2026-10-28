import { expect, it, vi } from 'vitest';
import { apiJson } from '@/lib/api/client';
import { enqueueVideos } from './enqueue';
vi.mock('@/lib/api/client', () => ({ apiJson: vi.fn() }));
it('retains only failed files and sends the selected languages and voice', async () => {
  const files = ['one', 'two', 'three'].map((name) => new File(['video'], name + '.mp4'));
  vi.mocked(apiJson)
    .mockResolvedValueOnce({ job_id: 'one' })
    .mockRejectedValueOnce(new Error('fixture'))
    .mockResolvedValueOnce({ job_id: 'three' });
  expect(await enqueueVideos(files, ['es', 'fr'], 'voice-id', false)).toEqual([files[1]]);
  const body = vi.mocked(apiJson).mock.calls[0][1]!.body as FormData;
  expect(body.get('langs')).toBe('es,fr');
  expect(body.get('voice_id')).toBe('voice-id');
  expect(body.get('preserve_bg')).toBe('false');
  expect(apiJson).toHaveBeenCalledTimes(3);
});
it('sends the quality tier only when one is chosen', async () => {
  vi.mocked(apiJson).mockReset().mockResolvedValue({ job_id: 'x' });
  const file = new File(['audio'], 'episode.mp3');
  await enqueueVideos([file], ['es'], '', true, undefined, 'quality');
  await enqueueVideos([file], ['es'], '', true);
  const [withTier, withoutTier] = vi
    .mocked(apiJson)
    .mock.calls.map((call) => call[1]!.body as FormData);
  expect(withTier.get('quality')).toBe('quality');
  expect(withoutTier.has('quality')).toBe(false);
});

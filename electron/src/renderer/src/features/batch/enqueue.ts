import { apiJson } from '@/lib/api/client';
import { beginAppActivity } from '@/lib/app-activity';
export async function enqueueVideos(
  files: File[],
  langs: string[],
  voice: string,
  preserve: boolean,
  onFailure?: (file: File, error: unknown) => void,
  quality = '',
) {
  const finishActivity = beginAppActivity('batch');
  const failed: File[] = [];
  try {
    for (const file of files) {
      const body = new FormData();
      body.set('video', file);
      body.set('langs', langs.join(','));
      if (voice) body.set('voice_id', voice);
      body.set('preserve_bg', String(preserve));
      if (quality) body.set('quality', quality);
      try {
        await apiJson('/batch/enqueue', { method: 'POST', body });
      } catch (error) {
        failed.push(file);
        onFailure?.(file, error);
      }
    }
    return failed;
  } finally {
    finishActivity();
  }
}

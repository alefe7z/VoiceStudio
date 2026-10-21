import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GitCompareArrowsIcon, NotebookPenIcon, StarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { WaveformPlayer } from '@/components/waveform-player';
import { useHistory, useSetHistoryNotes } from '@/hooks/use-history';
import { audioUrl } from '@/lib/api/client';
import type { HistoryItem } from '@/lib/api/types';
import { openTake } from '@/lib/store/takes';
import { formatRelative } from './format';

const NOTES_MAX = 20_000;
const sameScript = (a: string, b: string) =>
  a.trim().replace(/\s+/g, ' ') === b.trim().replace(/\s+/g, ' ');

/** Other takes of the same script, newest first: the versions of this line. */
export function takeVersions(item: HistoryItem, history: HistoryItem[]): HistoryItem[] {
  return history
    .filter(
      (other) => other.id !== item.id && other.audio_path && sameScript(other.text, item.text),
    )
    .sort((a, b) => Number(b.created_at) - Number(a.created_at));
}

export function TakeRevisions({ item }: { item: HistoryItem }) {
  const { t, i18n } = useTranslation();
  const history = useHistory();
  const saveNotes = useSetHistoryNotes();
  const [notes, setNotes] = useState(item.notes ?? '');
  const [savedNotes, setSavedNotes] = useState(item.notes ?? '');
  const versions = useMemo(() => takeVersions(item, history.data ?? []), [item, history.data]);
  const [compareId, setCompareId] = useState<string | null>(null);
  const compared = versions.find((version) => version.id === compareId) ?? null;
  const dirty = notes.trim() !== savedNotes.trim();

  const save = () => {
    const next = notes.trim();
    saveNotes.mutate(
      { id: item.id, notes: next },
      {
        onSuccess: (response) => {
          setSavedNotes(response.notes ?? '');
          setNotes(response.notes ?? '');
          openTake({ ...item, notes: response.notes });
        },
      },
    );
  };

  return (
    <div className="space-y-4">
      <section className="space-y-2" aria-labelledby={`take-notes-${item.id}`}>
        <h3 id={`take-notes-${item.id}`} className="flex items-center gap-2 text-sm font-medium">
          <NotebookPenIcon className="size-4 text-muted-foreground" aria-hidden="true" />
          {t('takeRevisions.notes_title')}
        </h3>
        <textarea
          aria-labelledby={`take-notes-${item.id}`}
          value={notes}
          maxLength={NOTES_MAX}
          rows={3}
          placeholder={t('takeRevisions.notes_placeholder')}
          onChange={(event) => setNotes(event.target.value)}
          className="w-full resize-y rounded-md border border-border/60 bg-background px-2.5 py-2 text-sm"
        />
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            disabled={!dirty || saveNotes.isPending}
            onClick={save}
          >
            {t(saveNotes.isPending ? 'common.loading' : 'takeRevisions.notes_save')}
          </Button>
        </div>
      </section>

      <section className="space-y-2" aria-labelledby={`take-versions-${item.id}`}>
        <h3 id={`take-versions-${item.id}`} className="flex items-center gap-2 text-sm font-medium">
          <GitCompareArrowsIcon className="size-4 text-muted-foreground" aria-hidden="true" />
          {t('takeRevisions.versions_title', { count: versions.length })}
        </h3>
        {versions.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('takeRevisions.versions_empty')}</p>
        ) : (
          <ul className="space-y-1">
            {versions.map((version) => (
              <li key={version.id} className="flex items-center gap-2 text-xs">
                <Button
                  size="xs"
                  variant={compareId === version.id ? 'secondary' : 'ghost'}
                  aria-pressed={compareId === version.id}
                  onClick={() => setCompareId(compareId === version.id ? null : version.id)}
                  className="min-w-0 flex-1 justify-start"
                >
                  {version.starred ? (
                    <StarIcon className="fill-current text-warning" aria-hidden="true" />
                  ) : null}
                  <span className="truncate">
                    {formatRelative(version.created_at, i18n.language)}
                  </span>
                  {version.notes ? (
                    <span className="truncate text-muted-foreground">· {version.notes}</span>
                  ) : null}
                </Button>
                <Button size="xs" variant="ghost" onClick={() => openTake(version)}>
                  {t('takeRevisions.open_version')}
                </Button>
              </li>
            ))}
          </ul>
        )}
        {compared && (
          <div className="grid gap-3 rounded-xl border border-border/60 bg-muted/15 p-3">
            <div className="space-y-1">
              <p className="text-xs font-medium">{t('takeRevisions.this_version')}</p>
              <WaveformPlayer
                src={audioUrl(item.audio_path)}
                source="history-compare-a"
                height={48}
              />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium">
                {t('takeRevisions.other_version', {
                  when: formatRelative(compared.created_at, i18n.language),
                })}
              </p>
              <WaveformPlayer
                src={audioUrl(compared.audio_path)}
                source="history-compare-b"
                height={48}
              />
              {compared.notes ? (
                <p className="whitespace-pre-wrap text-xs text-muted-foreground">
                  {compared.notes}
                </p>
              ) : null}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

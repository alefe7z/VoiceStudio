import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CircleAlertIcon,
  CircleCheckIcon,
  InfoIcon,
  LoaderCircleIcon,
  ShieldCheckIcon,
  TriangleAlertIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiJson, describeError } from '@/lib/api/client';

export type PreflightSeverity = 'error' | 'warning' | 'info';
export interface PreflightIssue {
  code: string;
  severity: PreflightSeverity;
  lang?: string;
  segment?: number;
  value?: string;
}
export interface PreflightReport {
  ready: boolean;
  counts: Record<PreflightSeverity, number>;
  issues: PreflightIssue[];
}

const ICONS = { error: CircleAlertIcon, warning: TriangleAlertIcon, info: InfoIcon } as const;
const TONES = {
  error: 'text-destructive',
  warning: 'text-warning',
  info: 'text-muted-foreground',
} as const;

/** Delivery checklist for one dub job; re-runs whenever `revision` changes. */
export function DubPreflight({
  jobId,
  revision,
  onReport,
}: {
  jobId: string;
  revision: string;
  onReport?(report: PreflightReport | null): void;
}) {
  const { t } = useTranslation();
  const [report, setReport] = useState<PreflightReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [run, setRun] = useState(0);
  const reportTo = useRef(onReport);
  reportTo.current = onReport;
  useEffect(() => {
    let live = true;
    setLoading(true);
    setError('');
    apiJson<PreflightReport>(`/dub/preflight/${encodeURIComponent(jobId)}`)
      .then((next) => {
        if (!live) return;
        setReport(next);
        reportTo.current?.(next);
      })
      .catch((reason) => {
        if (!live) return;
        setReport(null);
        reportTo.current?.(null);
        setError(describeError(reason));
      })
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [jobId, revision, run]);

  const order: PreflightSeverity[] = ['error', 'warning', 'info'];
  const issues = [...(report?.issues ?? [])].sort(
    (a, b) => order.indexOf(a.severity) - order.indexOf(b.severity),
  );
  return (
    <section aria-label={t('dubPreflight.title')} className="space-y-2 text-xs">
      <div className="flex items-center gap-2">
        <ShieldCheckIcon aria-hidden="true" className="size-3.5 text-muted-foreground" />
        <span className="font-medium">{t('dubPreflight.title')}</span>
        <Button
          size="xs"
          variant="ghost"
          className="ml-auto"
          disabled={loading}
          onClick={() => setRun((value) => value + 1)}
        >
          {loading ? <LoaderCircleIcon className="animate-spin" /> : null}
          {t('dubPreflight.recheck')}
        </Button>
      </div>
      {error && <p className="text-destructive">{error}</p>}
      {report && (
        <p role="status" className={report.ready ? 'text-success' : 'text-destructive'}>
          {report.ready ? (
            <CircleCheckIcon aria-hidden="true" className="mr-1 inline size-3.5" />
          ) : (
            <CircleAlertIcon aria-hidden="true" className="mr-1 inline size-3.5" />
          )}
          {t(report.ready ? 'dubPreflight.ready' : 'dubPreflight.blocked', {
            errors: report.counts.error,
            warnings: report.counts.warning,
          })}
        </p>
      )}
      {issues.length > 0 && (
        <ul className="max-h-40 space-y-1 overflow-y-auto">
          {issues.map((issue, index) => {
            const Icon = ICONS[issue.severity];
            return (
              <li
                key={`${issue.code}-${issue.lang}-${issue.segment}-${index}`}
                className="flex gap-1.5"
              >
                <Icon
                  aria-hidden="true"
                  className={`mt-0.5 size-3 shrink-0 ${TONES[issue.severity]}`}
                />
                <span>
                  {t(`dubPreflight.issue_${issue.code}`, {
                    lang: issue.lang?.toUpperCase(),
                    line: (issue.segment ?? 0) + 1,
                  })}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

import {
  CheckIcon,
  CoffeeIcon,
  CreditCardIcon,
  Globe2Icon,
  HeartIcon,
  LightbulbIcon,
  MailIcon,
  MessagesSquareIcon,
  RadioIcon,
  ShieldCheckIcon,
  StarIcon,
} from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { brandIcon } from '@/lib/brand';
import { DonationGoal } from './donation-goal';
import { ReportBug } from '@/components/report-bug';
import { ExternalLink } from '@/components/external-link';
import { GITHUB_SPONSORS_URL, KOFI_URL, PAYPAL_URL } from '@shared/utils/donateLinks';
import {
  ISSUES_URL,
  DISCORD_URL,
  SECURITY_URL,
  EMAIL,
  WEBSITE_URL,
  X_URL,
} from '@shared/utils/contactLinks';
import './support-settings.css';

export function SupportSettings() {
  const { t } = useTranslation();
  const [amount, setAmount] = useState<number | 'custom' | null>(null);
  const channels = [
    ['contact.feature_cta', ISSUES_URL, LightbulbIcon],
    ['contact.community_cta', DISCORD_URL, MessagesSquareIcon],
    ['contact.follow_cta', X_URL, RadioIcon],
    ['contact.security_cta', SECURITY_URL, ShieldCheckIcon],
    ['contact.email', 'mailto:' + EMAIL, MailIcon],
    ['contact.website', WEBSITE_URL, Globe2Icon],
  ] as const;

  return (
    <div className="support-studio">
      <header className="support-intro">
        <div className="support-emblem" aria-hidden="true">
          <img src={brandIcon} alt="" width={100} height={100} />
        </div>
        <h1>{t('donate.hero_title')}</h1>
        <p>{t('donate.footer')}</p>
      </header>

      <section className="support-giving" aria-label={t('donate.goal.title')}>
        <div className="support-progress">
          <DonationGoal />
        </div>
        <div className="support-checkout">
          <h2>{t('donate.suggested_title')}</h2>
          <div className="support-amounts" role="group" aria-label={t('donate.suggested_title')}>
            {[10, 20, 50, 'custom' as const].map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={amount === value}
                onClick={() => setAmount(amount === value ? null : value)}
              >
                <CheckIcon aria-hidden="true" className="support-selected" />
                <span>{value === 'custom' ? t('donate.custom') : '$' + value}</span>
              </button>
            ))}
          </div>
          <div className="support-payments" role="group" aria-label={t('donate.choose_method')}>
            <ExternalLink href={GITHUB_SPONSORS_URL}>
              <HeartIcon aria-hidden="true" />
              GitHub Sponsors
            </ExternalLink>
            <ExternalLink href={KOFI_URL}>
              <CoffeeIcon aria-hidden="true" />
              Ko-fi
            </ExternalLink>
            <ExternalLink
              href={typeof amount === 'number' ? PAYPAL_URL + '/' + amount : PAYPAL_URL}
            >
              <CreditCardIcon aria-hidden="true" />
              PayPal
            </ExternalLink>
          </div>
          <p className="support-payment-note">
            {typeof amount === 'number'
              ? t('donate.choose_method_amount', { amount })
              : t('donate.choose_method')}
          </p>
        </div>
      </section>

      <div className="support-community" role="group" aria-label={t('support.other_ways')}>
        <span>{t('support.other_ways')}</span>
        <ExternalLink href="https://github.com/debpalash/VoiceStudio">
          <StarIcon aria-hidden="true" />
          {t('support.star_github')}
        </ExternalLink>
        <ExternalLink href={DISCORD_URL}>
          <MessagesSquareIcon aria-hidden="true" />
          {t('support.join_discord')}
        </ExternalLink>
      </div>

      <section className="support-contact" aria-labelledby="support-contact-heading">
        <div className="support-contact-heading">
          <h2 id="support-contact-heading">{t('contact.channels_label')}</h2>
          <ReportBug />
        </div>
        <div className="support-channel-grid">
          {channels.map(([label, href, Icon]) => (
            <ExternalLink key={href} href={href}>
              <Icon aria-hidden="true" />
              <span>{t(label)}</span>
            </ExternalLink>
          ))}
        </div>
      </section>
    </div>
  );
}

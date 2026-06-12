import { useEffect, useState } from 'react';
import { useApp } from '../lib/store';
import { api } from '../lib/api';
import { t } from '../lib/i18n';
import { ACCENTS, FontSize, Lang, ThemeMode } from '../lib/settings';
import { Check, LogOut, Sparkles, Trash2, UserPlus, Smartphone } from 'lucide-react';
import AuthModal from '../components/AuthModal';

export default function ProfilePage() {
  const lang = useApp((s) => s.lang);
  const user = useApp((s) => s.user);
  const billing = useApp((s) => s.billing);
  const refreshUser = useApp((s) => s.refreshUser);
  const refreshBilling = useApp((s) => s.refreshBilling);
  const openPaywall = useApp((s) => s.openPaywall);
  const setTheme = useApp((s) => s.setTheme);
  const setAccent = useApp((s) => s.setAccent);
  const setFontSize = useApp((s) => s.setFontSize);
  const setLang = useApp((s) => s.setLang);
  const accentId = useApp((s) => s.accentId);
  const theme = useApp((s) => s.theme);
  const fontSize = useApp((s) => s.fontSize);
  const signOut = useApp((s) => s.signOut);

  const [about, setAbout] = useState(user?.profile?.about_me || '');
  const [saving, setSaving] = useState(false);
  const [savedFlag, setSavedFlag] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);

  useEffect(() => { refreshBilling().catch(() => {}); }, [refreshBilling]);
  useEffect(() => { setAbout(user?.profile?.about_me || ''); }, [user?.id, user?.profile?.about_me]);

  async function save() {
    setSaving(true);
    try {
      await api.updateMe({ self_description: about });
      await refreshUser();
      setSavedFlag(true);
      setTimeout(() => setSavedFlag(false), 1800);
    } catch {} finally { setSaving(false); }
  }

  async function deleteAccount() {
    try { await api.deleteAccount(); } catch {}
    setConfirmDel(false);
    await signOut();
  }

  const tier = billing?.sub_type || 'free';
  const tierLabel = tier === 'pro' ? t('profile.pro', lang) : tier === 'trial' ? t('profile.trial', lang) : t('profile.free', lang);

  return (
    <div className="space-y-5 sm:space-y-6 max-w-5xl" data-testid="profile-page">
      {/* Accent swatches + theme card */}
      <section className="card-surface rounded-3xl p-4 sm:p-5 space-y-4 sm:space-y-5">
        <div>
          <div className="muted-text text-xs uppercase tracking-wider mb-3">{t('profile.accent', lang)}</div>
          <div className="flex gap-3 flex-wrap">
            {ACCENTS.map((a) => (
              <button
                key={a.id}
                data-testid={`accent-${a.id}`}
                onClick={() => setAccent(a.id)}
                className="w-11 h-11 rounded-full flex items-center justify-center transition-transform hover:scale-105"
                style={{ background: a.hex, boxShadow: accentId === a.id ? `0 0 0 3px rgba(255,255,255,0.10), 0 0 0 5px ${a.hex}80` : undefined }}
              >
                {accentId === a.id && <Check className="w-5 h-5 text-white" />}
              </button>
            ))}
          </div>
        </div>
        <div className="h-px divider border-t" />
        <Row label={t('profile.theme', lang)}>
          <Toggle
            on={theme === 'dark'}
            onChange={(v) => setTheme(v ? 'dark' : 'light' as ThemeMode)}
            testId="theme-toggle"
          />
        </Row>
        <div className="h-px divider border-t" />
        <Row label={t('profile.fontSize', lang)}>
          <div className="flex gap-1">
            {(['small', 'medium', 'large'] as FontSize[]).map((s) => (
              <button key={s}
                      onClick={() => setFontSize(s)}
                      data-testid={`font-${s}`}
                      className={'btn-pill text-sm !py-1 ' + (fontSize === s ? 'btn-soft accent-text' : 'btn-ghost')}>
                {s === 'small' ? 'A−' : s === 'medium' ? 'A' : 'A+'}
              </button>
            ))}
          </div>
        </Row>
        <div className="h-px divider border-t" />
        <Row label={t('profile.language', lang)}>
          <div className="flex gap-1">
            {(['ru', 'en'] as Lang[]).map((l) => (
              <button key={l}
                      onClick={() => setLang(l)}
                      data-testid={`lang-${l}`}
                      className={'btn-pill text-sm !py-1 px-3 uppercase ' + (lang === l ? 'btn-soft accent-text' : 'btn-ghost')}>
                {l}
              </button>
            ))}
          </div>
        </Row>
      </section>

      {/* Tier card */}
      <section className="card-surface rounded-3xl p-4 sm:p-5" data-testid="tier-card">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl accent-bg flex items-center justify-center text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-lg">{tierLabel}</div>
            {tier === 'free' && billing && (
              <div className="muted-text text-sm mt-1">
                {t('profile.weeklyLeft', lang)} {billing.analyses_left_this_week ?? '—'}
              </div>
            )}
            {tier === 'trial' && billing?.trial_days_left !== undefined && (
              <div className="muted-text text-sm mt-1">
                {lang === 'ru' ? `Дней триала осталось: ${billing.trial_days_left}` : `Trial days left: ${billing.trial_days_left}`}
              </div>
            )}
            {tier !== 'pro' && (
              <button onClick={() => openPaywall(t('profile.upgradeCta', lang))} className="btn-pill btn-soft mt-3" data-testid="upgrade-cta">
                <Sparkles className="w-4 h-4" />
                {t('profile.upgradeCta', lang)}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* About me */}
      <section className="card-surface rounded-3xl p-4 sm:p-5" data-testid="about-section">
        <div className="font-display text-lg mb-2">{t('profile.about', lang)}</div>
        <p className="muted-text text-sm mb-3">{t('profile.aboutHint', lang)}</p>
        <textarea
          value={about}
          onChange={(e) => setAbout(e.target.value)}
          rows={5}
          maxLength={1000}
          className="input-base resize-none"
          data-testid="about-input"
        />
        <div className="flex items-center justify-between mt-3">
          <span className="muted-text text-xs">{about.length}/1000</span>
          <div className="flex items-center gap-2">
            {savedFlag && <span className="text-sm accent-text">{t('profile.saved', lang)}</span>}
            <button onClick={save} disabled={saving} className="btn-pill btn-primary" data-testid="about-save-btn">
              {t('profile.save', lang)}
            </button>
          </div>
        </div>
      </section>

      {/* Account section */}
      <section className="card-surface rounded-3xl p-5">
        {user?.is_anonymous ? (
          <>
            <div className="font-display text-lg mb-1">{t('profile.createAccount', lang)}</div>
            <p className="muted-text text-sm mb-4">{t('profile.createAccountDesc', lang)}</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setAuthOpen(true)} className="btn-pill btn-primary" data-testid="register-btn">
                <UserPlus className="w-4 h-4" />
                {t('profile.signIn', lang)}
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="font-semibold truncate">
                {user?.email
                  || [user?.first_name, user?.last_name].filter(Boolean).join(' ')
                  || (lang === 'ru' ? 'Аккаунт' : 'Account')}
              </div>
              <div className="muted-text text-sm">
                {user?.email
                  ? (user?.email_verified
                      ? (lang === 'ru' ? 'Email подтверждён' : 'Email verified')
                      : (lang === 'ru' ? 'Email не подтверждён' : 'Email not verified'))
                  : (user?.linked_providers?.includes('telegram')
                      ? 'Telegram'
                      : user?.linked_providers?.includes('google')
                        ? 'Google'
                        : (lang === 'ru' ? 'Авторизован' : 'Signed in'))}
              </div>
            </div>
            <button onClick={signOut} className="btn-pill btn-ghost shrink-0" data-testid="signout-btn">
              <LogOut className="w-4 h-4" />
              {t('profile.signOut', lang)}
            </button>
          </div>
        )}
      </section>

      {/* Mobile app */}
      <section className="card-surface rounded-3xl p-4 sm:p-5" data-testid="mobile-app-section">
        <div className="flex items-start gap-4">
          <img
            src="/icon-background.png"
            alt=""
            aria-hidden="true"
            className="w-12 h-12 rounded-2xl object-cover shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="font-display text-lg mb-1">
              {lang === 'ru' ? 'Мобильное приложение' : 'Mobile app'}
            </div>
            <p className="muted-text text-sm mb-4">
              {lang === 'ru'
                ? 'Записывайте сны утром, прямо в постели. Один аккаунт — все ваши сны на любом устройстве.'
                : 'Capture dreams the moment you wake. One account — same dreams on every device.'}
            </p>
            <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2">
              <a
                href="https://github.com/core-euler/sna_net/releases/tag/v0.4.2"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-pill btn-soft !py-2 w-full sm:w-auto justify-center sm:justify-start"
                data-testid="download-android-btn"
              >
                <Smartphone className="w-4 h-4" />
                {lang === 'ru' ? 'Скачать для Android' : 'Download for Android'}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Danger zone */}
      {!user?.is_anonymous && (
        <section className="rounded-3xl p-5 border" style={{ borderColor: 'rgba(239,68,68,0.25)' }}>
          <div className="font-display text-lg mb-2 text-red-300">{t('profile.dangerZone', lang)}</div>
          <button onClick={() => setConfirmDel(true)} className="btn-pill bg-red-500/15 text-red-300 hover:bg-red-500/25" data-testid="delete-account-btn">
            <Trash2 className="w-4 h-4" />
            {t('profile.deleteAccount', lang)}
          </button>
        </section>
      )}

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />

      {confirmDel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setConfirmDel(false)} />
          <div className="glass relative rounded-3xl p-6 max-w-sm w-full text-center">
            <p className="mb-5">{lang === 'ru' ? 'Удалить аккаунт и все сны без возможности восстановления?' : 'Delete your account and all dreams permanently?'}</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => setConfirmDel(false)} className="btn-pill btn-ghost">{t('common.cancel', lang)}</button>
              <button onClick={deleteAccount} className="btn-pill bg-red-500 hover:bg-red-600 text-white" data-testid="confirm-delete-btn">
                {t('dream.delete', lang)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-base">{label}</span>
      {children}
    </div>
  );
}

function Toggle({ on, onChange, testId }: { on: boolean; onChange: (v: boolean) => void; testId?: string }) {
  return (
    <button
      onClick={() => onChange(!on)}
      data-testid={testId}
      className={'w-12 h-7 rounded-full relative ' + (on ? 'accent-bg' : 'tgl-track')}
    >
      <span
        className="tgl-knob absolute top-0.5 left-0.5 w-6 h-6 rounded-full"
        style={{ transform: on ? 'translateX(20px)' : 'translateX(0)' }}
      />
    </button>
  );
}

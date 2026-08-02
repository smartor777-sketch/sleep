import { useCallback, useEffect, useState } from 'react';
import { useApp } from '../lib/store';
import { api, ApiError } from '../lib/api';
import { AdminStats, AdminUser } from '../lib/types';
import { Loader2, RefreshCw, Search, Shield, UserPlus, KeyRound } from 'lucide-react';

export default function AdminPage() {
  const lang = useApp((s) => s.lang);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create user form
  const [showCreate, setShowCreate] = useState(false);
  const [cEmail, setCEmail] = useState('');
  const [cPassword, setCPassword] = useState('');
  const [cName, setCName] = useState('');
  const [cBusy, setCBusy] = useState(false);
  const [cMsg, setCMsg] = useState<string | null>(null);

  // Per-user actions
  const [resetResult, setResetResult] = useState<{ user_id: string; email?: string; new_password: string } | null>(null);
  const [actionBusy, setActionBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, u] = await Promise.all([
        api.adminStats(),
        api.adminUsers({ q: q || undefined, limit: 200 }),
      ]);
      setStats(s);
      setUsers(u.items);
      setTotal(u.total);
    } catch (e) {
      const ae = e as ApiError;
      setError(ae.detail || ae.message || 'admin_load_failed');
    } finally {
      setLoading(false);
    }
  }, [q]);

  useEffect(() => { load(); }, [load]);

  async function createUser() {
    setCBusy(true);
    setCMsg(null);
    try {
      await api.adminCreateUser({ email: cEmail.trim(), password: cPassword, first_name: cName.trim() || undefined });
      setCMsg(lang === 'ru' ? 'Пользователь создан' : 'User created');
      setCEmail(''); setCPassword(''); setCName(''); setShowCreate(false);
      load();
    } catch (e) {
      const ae = e as ApiError;
      setCMsg(ae.detail || ae.message || 'create_failed');
    } finally { setCBusy(false); }
  }

  async function resetPassword(u: AdminUser) {
    setActionBusy(u.id);
    setError(null);
    try {
      const r = await api.adminResetPassword(u.id);
      setResetResult(r);
    } catch (e) {
      const ae = e as ApiError;
      setError(ae.detail || ae.message || 'reset_failed');
    } finally { setActionBusy(null); }
  }

  async function toggleAdmin(u: AdminUser) {
    setActionBusy(u.id);
    setError(null);
    try {
      await api.adminUpdateUser(u.id, { is_admin: !u.is_admin });
      load();
    } catch (e) {
      const ae = e as ApiError;
      setError(ae.detail || ae.message || 'update_failed');
    } finally { setActionBusy(null); }
  }

  async function toggleActive(u: AdminUser) {
    setActionBusy(u.id);
    setError(null);
    try {
      await api.adminUpdateUser(u.id, { is_active: !u.is_active });
      load();
    } catch (e) {
      const ae = e as ApiError;
      setError(ae.detail || ae.message || 'update_failed');
    } finally { setActionBusy(null); }
  }

  return (
    <div className="space-y-5 max-w-6xl" data-testid="admin-page">
      <div className="flex items-center justify-between gap-3">
        <div className="font-display text-xl sm:text-2xl">
          {lang === 'ru' ? 'Админ-панель' : 'Admin panel'}
        </div>
        <button onClick={load} disabled={loading} className="btn-pill btn-ghost !py-2" data-testid="admin-refresh">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {lang === 'ru' ? 'Обновить' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 rounded-xl px-3 py-2" data-testid="admin-error">{error}</div>
      )}

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="admin-stats">
          <StatCard label={lang === 'ru' ? 'Юзеры' : 'Users'} value={stats.total_users} />
          <StatCard label={lang === 'ru' ? 'Сны' : 'Dreams'} value={stats.total_dreams} />
          <StatCard label={lang === 'ru' ? 'Анализы' : 'Analyses'} value={stats.total_analyses} />
          <StatCard label={lang === 'ru' ? 'Анонимы' : 'Anonymous'} value={stats.total_anonymous} />
          <StatCard label={lang === 'ru' ? 'Premium' : 'Premium'} value={stats.total_premium} />
          <StatCard label={lang === 'ru' ? 'Актив за 7д' : 'Active 7d'} value={stats.active_last_7d} />
        </div>
      )}

      {/* Create user */}
      <section className="card-surface rounded-3xl p-4 sm:p-5">
        <button
          onClick={() => setShowCreate((v) => !v)}
          className="btn-pill btn-soft !py-2"
          data-testid="admin-create-toggle"
        >
          <UserPlus className="w-4 h-4" />
          {lang === 'ru' ? 'Создать пользователя' : 'Create user'}
        </button>
        {showCreate && (
          <div className="flex flex-col sm:flex-row gap-2 mt-3">
            <input value={cName} onChange={(e) => setCName(e.target.value)} placeholder={lang === 'ru' ? 'Имя' : 'Name'} className="input-base" data-testid="admin-create-name" />
            <input value={cEmail} onChange={(e) => setCEmail(e.target.value)} placeholder="Email" type="email" className="input-base" data-testid="admin-create-email" />
            <input value={cPassword} onChange={(e) => setCPassword(e.target.value)} placeholder={lang === 'ru' ? 'Пароль (мин. 8)' : 'Password (min 8)'} type="password" className="input-base" data-testid="admin-create-password" />
            <button onClick={createUser} disabled={cBusy || !cEmail || !cPassword || cPassword.length < 8} className="btn-pill btn-primary shrink-0 disabled:opacity-50" data-testid="admin-create-submit">
              {cBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {lang === 'ru' ? 'Создать' : 'Create'}
            </button>
          </div>
        )}
        {cMsg && <div className={`mt-2 text-sm ${cMsg.startsWith('Пользователь') || cMsg.startsWith('User') ? 'text-green-400' : 'text-red-400'}`} data-testid="admin-create-msg">{cMsg}</div>}
      </section>

      {/* Reset password result */}
      {resetResult && (
        <section className="rounded-3xl p-5 border" style={{ borderColor: 'rgba(250,144,66,0.3)' }} data-testid="admin-reset-result">
          <div className="flex items-center gap-2 font-display text-lg mb-1">
            <KeyRound className="w-5 h-5" />
            {lang === 'ru' ? 'Новый пароль выдан' : 'New password issued'}
          </div>
          <p className="muted-text text-sm mb-2">
            {lang === 'ru'
              ? `Пользователю ${resetResult.email || resetResult.user_id} установлен новый пароль. Передайте его пользователю.`
              : `User ${resetResult.email || resetResult.user_id} got a new password. Share it with the user.`}
          </p>
          <code className="text-lg font-semibold accent-text break-all">{resetResult.new_password}</code>
          <button onClick={() => setResetResult(null)} className="btn-pill btn-ghost !py-1 mt-3">{lang === 'ru' ? 'Понятно' : 'Dismiss'}</button>
        </section>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={lang === 'ru' ? 'Поиск по email, имени, device_id…' : 'Search by email, name, device_id…'}
          className="input-base pl-9"
          data-testid="admin-search"
        />
      </div>

      {/* Users table */}
      <section className="card-surface rounded-3xl overflow-hidden">
        <div className="px-4 py-3 text-sm muted-text border-b border-white/5">
          {lang === 'ru' ? `Пользователей: ${total}` : `Users: ${total}`}
        </div>
        {users.length === 0 && !loading ? (
          <div className="p-6 text-center muted-text text-sm">{lang === 'ru' ? 'Никого не найдено' : 'Nothing found'}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left muted-text text-xs uppercase tracking-wider border-b border-white/5">
                  <th className="px-4 py-2.5">{lang === 'ru' ? 'Имя' : 'Name'}</th>
                  <th className="px-4 py-2.5">Email</th>
                  <th className="px-4 py-2.5">{lang === 'ru' ? 'Сны' : 'Dreams'}</th>
                  <th className="px-4 py-2.5">{lang === 'ru' ? 'Подписка' : 'Plan'}</th>
                  <th className="px-4 py-2.5">{lang === 'ru' ? 'Статус' : 'Status'}</th>
                  <th className="px-4 py-2.5">{lang === 'ru' ? 'Действия' : 'Actions'}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-white/5 hover:bg-white/5">
                    <td className="px-4 py-2.5">
                      <div className="font-medium">
                        {[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}
                        {u.is_admin && <Shield className="inline w-4 h-4 ml-1.5 accent-text" />}
                      </div>
                      <div className="muted-text text-xs">{u.is_anonymous ? (lang === 'ru' ? 'аноним' : 'anonymous') : u.created_at.slice(0, 10)}</div>
                    </td>
                    <td className="px-4 py-2.5">{u.email || '—'}</td>
                    <td className="px-4 py-2.5">{u.dreams_count}</td>
                    <td className="px-4 py-2.5">{u.sub_type}</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'}`}>
                        {u.is_active ? (lang === 'ru' ? 'активен' : 'active') : (lang === 'ru' ? 'заблокирован' : 'blocked')}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex gap-1.5 flex-wrap">
                        <button
                          onClick={() => resetPassword(u)}
                          disabled={actionBusy === u.id}
                          className="btn-pill btn-soft !py-1 text-xs"
                          data-testid={`reset-pw-${u.id}`}
                        >
                          {actionBusy === u.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <KeyRound className="w-3 h-3" />}
                          {lang === 'ru' ? 'Пароль' : 'Password'}
                        </button>
                        <button
                          onClick={() => toggleAdmin(u)}
                          disabled={actionBusy === u.id}
                          className="btn-pill btn-soft !py-1 text-xs"
                          data-testid={`toggle-admin-${u.id}`}
                        >
                          <Shield className="w-3 h-3" />
                          {u.is_admin ? (lang === 'ru' ? 'снять админа' : 'unadmin') : (lang === 'ru' ? 'админ' : 'admin')}
                        </button>
                        <button
                          onClick={() => toggleActive(u)}
                          disabled={actionBusy === u.id}
                          className="btn-pill btn-soft !py-1 text-xs"
                          data-testid={`toggle-active-${u.id}`}
                        >
                          {u.is_active ? (lang === 'ru' ? 'блокировать' : 'block') : (lang === 'ru' ? 'разблокировать' : 'unblock')}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card-surface rounded-2xl p-4">
      <div className="text-2xl font-bold">{value}</div>
      <div className="muted-text text-xs">{label}</div>
    </div>
  );
}

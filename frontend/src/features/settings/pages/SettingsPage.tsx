import { useEffect, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { apiClient } from '@/infrastructure/api/client';

const LANGS = ['ru', 'en', 'sk', 'pl'];

const urlBase64ToUint8Array = (base64String: string) => {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

export const SettingsPage = () => {
  const { t } = useLanguage();
  const [user, setUser] = useState<any>(null);
  const [sys, setSys] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pushMsg, setPushMsg] = useState<string | null>(null);

  const load = async () => {
    try {
      const [u, s] = await Promise.all([
        apiClient.get('/settings/user'),
        apiClient.get('/settings'),
      ]);
      setUser(u.data);
      setSys(s.data);
    } catch (e: any) {
      setError(e && e.message ? e.message : 'Failed to load settings');
    }
  };
  useEffect(() => { load(); }, []);

  const saveUser = async (patch: any) => {
    setMsg(null);
    try {
      const r = await apiClient.put('/settings/user', patch);
      setUser(r.data);
      setMsg('Сохранено');
    } catch (e: any) {
      setMsg('Ошибка сохранения');
    }
  };

  const enablePush = async () => {
    setPushMsg(null);
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        setPushMsg('Браузер не поддерживает push-уведомления');
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setPushMsg('Разрешение на уведомления не выдано');
        return;
      }
      const reg = await navigator.serviceWorker.register('/sw.js');
      const { data } = await apiClient.get('/notifications/webpush/public-key');
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(data.public_key),
      });
      await apiClient.post('/notifications/webpush/subscribe', { subscription: sub.toJSON() });
      setPushMsg('Уведомления включены');
    } catch (e: any) {
      setPushMsg('Ошибка включения: ' + (e?.message || ''));
    }
  };

  const sendTestPush = async () => {
    try {
      await apiClient.post('/notifications/webpush/test');
      setPushMsg('Тестовое уведомление отправлено');
    } catch (e: any) {
      setPushMsg('Ошибка теста: ' + (e?.response?.data?.detail || e?.message || ''));
    }
  };

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold mb-6">{t('settings')}</h1>
      {error && <div className="auth-error mb-4"><span>{error}</span></div>}
      {user && (
        <div className="card mb-4">
          <h2 className="text-lg font-medium mb-3">Профиль</h2>
          <div className="space-y-3">
            <label className="block text-sm text-muted">Язык</label>
            <select className="auth-input" value={user.language} onChange={(e) => saveUser({ language: e.target.value })}>
              {LANGS.map((l) => <option key={l} value={l}>{l.toUpperCase()}</option>)}
            </select>

            <label className="block text-sm text-muted">Тема</label>
            <select className="auth-input" value={user.theme} onChange={(e) => saveUser({ theme: e.target.value })}>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!user.notifications_enabled} onChange={(e) => saveUser({ notifications_enabled: e.target.checked })} />
              Уведомления
            </label>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!user.email_notifications} onChange={(e) => saveUser({ email_notifications: e.target.checked })} />
              Email-уведомления
            </label>

            <label className="block text-sm text-muted">Элементов на странице</label>
            <input className="auth-input" type="number" value={user.items_per_page} onChange={(e) => saveUser({ items_per_page: Number(e.target.value) })} />

            {msg && <p className="text-xs text-muted">{msg}</p>}
          </div>
        </div>
      )}

      <div className="card mb-4">
        <h2 className="text-lg font-medium mb-3">Уведомления (Web-Push)</h2>
        <p className="text-sm text-muted mb-3">Браузерные push-уведомления о выгодных грузах.</p>
        <div className="flex gap-2 mb-2">
          <button type="button" onClick={enablePush} className="btn btn-primary">Включить уведомления</button>
          <button type="button" onClick={sendTestPush} className="btn">Отправить тестовое</button>
        </div>
        {pushMsg && <p className="text-xs text-muted">{pushMsg}</p>}
      </div>

      {sys && (
        <div className="card">
          <h2 className="text-lg font-medium mb-3">Системные настройки</h2>
          <ul className="text-sm space-y-1 text-muted">
            <li>Валюта: {sys.default_currency}</li>
            <li>Язык по умолчанию: {sys.default_language}</li>
            <li>Лимит email/час: {sys.max_email_per_hour}</li>
            <li>Интервал email (с): {sys.email_delay_seconds}</li>
            <li>Цена топлива (€/л): {sys.fuel_price_per_liter}</li>
            <li>Интервал GPS (мин): {sys.gps_sync_interval_minutes}</li>
            <li>Интервал скрапинга (мин): {sys.scraping_interval_minutes}</li>
          </ul>
        </div>
      )}
    </div>
  );
};
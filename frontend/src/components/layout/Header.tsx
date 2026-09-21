import { useState, useEffect } from 'react';
import { Bell, Search, User, Moon, Sun } from 'lucide-react';
import { apiClient } from '@/infrastructure/api/client';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { Lang } from '@/infrastructure/i18n/translations';

export const Header = () => {
  const { theme, toggleTheme } = useTheme();
  const { lang, setLang, t } = useLanguage();
  const [bellOpen, setBellOpen] = useState(false);
  const [notifs, setNotifs] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    apiClient.get('/notifications/preferences').then((r) => {
      const prefs = r.data || {};
      const items = [];
      items.push({ title: 'Уведомления о выгодных грузах', body: prefs.profitable_cargo ? 'Включены' : 'Выключены' });
      items.push({ title: 'Оповещения плана', body: prefs.plan_alert ? 'Включены' : 'Выключены' });
      items.push({ title: 'Web-Push', body: prefs.push_enabled ? 'Доступен' : 'Отключён' });
      setNotifs(items);
      setUnread(prefs.profitable_cargo ? 1 : 0);
    }).catch(() => {});
  }, []);

  return (
    <header className="header">
      <div className="header-search">
        <Search size={18} className="search-icon" />
        <input
          type="text"
          placeholder={t('search')}
          className="search-input"
        />
      </div>

      <div className="header-actions">
        <select
          className="lang-select"
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
        >
          <option value="ru">RU</option>
          <option value="en">EN</option>
          <option value="sk">SK</option>
          <option value="pl">PL</option>
        </select>

        <button
          className="icon-btn"
          onClick={toggleTheme}
          title={theme === 'dark' ? "Включить светлую тему" : "Включить темную тему"}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <button
          className="icon-btn"
          onClick={() => setBellOpen(!bellOpen)}
          title="Уведомления"
        >
          <Bell size={20} />
          {unread > 0 && <span className="notification-badge">{unread}</span>}
        </button>

        {bellOpen && (
          <div className="absolute right-16 top-14 w-72 card shadow-lg z-50 p-3">
            <p className="text-sm font-semibold mb-2">Уведомления</p>
            {notifs.length === 0 ? (
              <p className="text-xs text-muted">Новых уведомлений нет</p>
            ) : (
              <ul className="space-y-2">
                {notifs.map((n, i) => (
                  <li key={i} className="text-xs border-b border-border pb-1">
                    <p className="font-medium">{n.title}</p>
                    <p className="text-muted">{n.body}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="user-profile">
          <div className="avatar">
            <User size={20} />
          </div>
          <div className="user-info">
            <span className="user-name">Администратор</span>
            <span className="user-role">Super Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
};

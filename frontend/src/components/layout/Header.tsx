import { Bell, Search, User, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { Lang } from '@/infrastructure/i18n/translations';

export const Header = () => {
  const { theme, toggleTheme } = useTheme();
  const { lang, setLang, t } = useLanguage();

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

        <button className="icon-btn">
          <Bell size={20} />
          <span className="notification-badge">2</span>
        </button>

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

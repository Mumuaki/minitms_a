import { Bell, Search, User, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

export const Header = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="header">
      <div className="header-search">
        <Search size={18} className="search-icon" />
        <input 
          type="text" 
          placeholder="Поиск..." 
          className="search-input"
        />
      </div>

      <div className="header-actions">
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

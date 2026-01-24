import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Users, 
  LayoutDashboard, 
  Settings, 
  Truck, 
  Package, 
  FileText, 
  LogOut 
} from 'lucide-react';

const MENU_ITEMS = [
  { icon: LayoutDashboard, label: 'Дашборд', path: '/' },
  { icon: Users, label: 'Пользователи', path: '/users' },
  { icon: Truck, label: 'Автопарк', path: '/fleet' },
  { icon: Package, label: 'Грузы', path: '/loads' },
  { icon: FileText, label: 'Отчеты', path: '/reports' },
  { icon: Settings, label: 'Настройки', path: '/settings' },
];

export const Sidebar = () => {
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.reload();
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-text">
          Mini<span className="text-primary">TMS</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {MENU_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button onClick={handleLogout} className="nav-item logout-btn">
          <LogOut size={20} />
          <span>Выйти</span>
        </button>
      </div>
    </aside>
  );
};

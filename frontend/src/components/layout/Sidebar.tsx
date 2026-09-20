import { NavLink } from 'react-router-dom';
import {
  Users,
  LayoutDashboard,
  Settings,
  Truck,
  Package,
  FileText,
  LogOut,
  DollarSign,
  Navigation
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

const MENU_ITEMS = [
  { icon: LayoutDashboard, key: 'dashboard', path: '/' },
  { icon: Users, key: 'users', path: '/users' },
  { icon: Truck, key: 'fleet', path: '/fleet' },
  { icon: Navigation, key: 'gps', path: '/gps' },
  { icon: Package, key: 'loads', path: '/loads' },
  { icon: DollarSign, key: 'finance', path: '/finance' },
  { icon: FileText, key: 'reports', path: '/reports' },
  { icon: Settings, key: 'settings', path: '/settings' },
];

export const Sidebar = () => {
  const { t } = useLanguage();

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
            <span>{t(item.key)}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button onClick={handleLogout} className="nav-item logout-btn">
          <LogOut size={20} />
          <span>{t('logout')}</span>
        </button>
      </div>
    </aside>
  );
};

import React from 'react';
import { Edit2, Trash2, CheckCircle, XCircle } from 'lucide-react';
import { User } from '../types';

interface UsersTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (id: number) => void;
}

export const UsersTable = ({ users, onEdit, onDelete }: UsersTableProps) => {
  const getRoleBadge = (role: string) => {
    const styles: Record<string, string> = {
      administrator: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      director: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      dispatcher: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      guest: 'bg-green-500/20 text-green-300 border-green-500/30',
    };
    
    // Fallback style
    const style = styles[role] || 'bg-gray-500/20 text-gray-300 border-gray-500/30';

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${style}`}>
        {role.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Пользователь</th>
            <th>Email</th>
            <th>Роль</th>
            <th>Статус</th>
            <th className="text-right">Действия</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td className="text-muted">#{user.id}</td>
              <td>
                <div className="font-medium">{user.username}</div>
              </td>
              <td className="text-muted">{user.email}</td>
              <td>{getRoleBadge(user.role)}</td>
              <td>
                {user.is_active ? (
                  <div className="flex items-center gap-2 text-success text-sm">
                    <CheckCircle size={14} /> Активен
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-error text-sm">
                    <XCircle size={14} /> Неактивен
                  </div>
                )}
              </td>
              <td>
                <div className="flex justify-end gap-2">
                  <button 
                    onClick={() => onEdit(user)}
                    className="icon-btn hover:bg-white/10 text-blue-400"
                    title="Редактировать"
                  >
                    <Edit2 size={16} />
                  </button>
                  {/* Кнопка удаления может быть скрыта для самого себя или superadmin */}
                  <button 
                    onClick={() => onDelete(user.id)}
                    className="icon-btn hover:bg-white/10 text-red-400"
                    title="Удалить"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
          {users.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center py-8 text-muted">
                Пользователи не найдены
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

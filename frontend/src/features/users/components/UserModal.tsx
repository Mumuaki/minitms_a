import React, { useState, useEffect } from 'react';
import { User, CreateUserRequest, UpdateUserRequest } from '../types';
import { Modal } from '@/components/ui/Modal';
import '@/features/auth/styles.css'; // Reusing form styles

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void>;
  user?: User | null; // If provided, we are in Edit mode
}

export const UserModal = ({ isOpen, onClose, onSubmit, user }: UserModalProps) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'dispatcher',
    language: 'ru',
    is_active: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '', // Password not shown in edit
        role: user.role,
        language: user.language || 'ru',
        is_active: user.is_active
      });
    } else {
      // Reset for create mode
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'dispatcher',
        language: 'ru',
        is_active: true
      });
    }
    setError(null);
  }, [user, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Prepare payload
      const payload: any = {
        username: formData.username,
        email: formData.email,
        role: formData.role,
        language: formData.language,
        is_active: formData.is_active
      };

      // Only add password if it's set (required for create, optional for update)
      if (formData.password) {
        payload.password = formData.password;
      } else if (!user) {
        throw new Error('Пароль обязателен для нового пользователя');
      }

      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Ошибка сохранения');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={user ? 'Редактирование пользователя' : 'Новый пользователь'}
    >
      <form onSubmit={handleSubmit}>
        <div className="modal-body">
          {error && (
            <div className="auth-error mb-4">
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Имя пользователя (ФИО)</label>
            <input
              type="text"
              className="auth-input"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="auth-input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              {user ? 'Пароль (оставьте пустым, чтобы не менять)' : 'Пароль'}
            </label>
            <input
              type="password"
              className="auth-input"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required={!user}
              minLength={6}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Роль</label>
            <select
              className="auth-input"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="dispatcher">Диспетчер</option>
              <option value="director">Директор</option>
              <option value="guest">Гость</option>
              <option value="administrator">Администратор</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Язык интерфейса</label>
            <select
              className="auth-input"
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
            >
              <option value="ru">Русский (RU)</option>
              <option value="en">English (EN)</option>
              <option value="sk">Slovenčina (SK)</option>
              <option value="pl">Polski (PL)</option>
            </select>
          </div>

          <div className="form-group flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              style={{ width: 'auto' }}
            />
            <label htmlFor="is_active" className="form-label mb-0" style={{ marginBottom: 0 }}>
              Активен
            </label>
          </div>
        </div>

        <div className="modal-footer">
          <button 
            type="button" 
            className="btn btn-outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Отмена
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Сохранение...' : (user ? 'Сохранить' : 'Создать')}
          </button>
        </div>
      </form>
    </Modal>
  );
};

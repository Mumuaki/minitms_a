import React, { useState } from 'react';
import { Mail, Lock, AlertCircle, ArrowRight } from 'lucide-react';
import { authService } from '../services/authService';
import '../styles.css';

export const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await authService.login({ email, password });
      
      // Сохраняем токены
      localStorage.setItem('access_token', response.access_token);
      // Если есть refresh token, его тоже стоит сохранить. В текущем API login возвращает access_token и token_type.
      // Проверим ответ в authService.ts (TokenResponse)

      // Временный редирект (пока нет полноценного роутинга)
      window.location.reload(); 
    } catch (err: any) {
      console.error('Login error:', err);
      // Простая обработка ошибок
      let message = 'Произошла ошибка при входе';
      if (err.response?.status === 401) {
        message = 'Неверный email или пароль';
      } else if (err.message) {
        message = err.message;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      {error && (
        <div className="auth-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="form-group">
        <label className="form-label" htmlFor="email">Email</label>
        <div className="input-wrapper">
          <Mail className="input-icon" size={20} />
          <input
            id="email"
            type="email" // Changed from text to email for better UX
            className="auth-input"
            placeholder="name@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="password">Пароль</label>
        <div className="input-wrapper">
          <Lock className="input-icon" size={20} />
          <input
            id="password"
            type="password"
            className="auth-input"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <a href="#" className="forgot-password">Забыли пароль?</a>
      </div>

      <button 
        type="submit" 
        className="btn btn-primary btn-auth"
        disabled={isLoading}
      >
        {isLoading ? (
          <div className="loader" />
        ) : (
          <>
            <span>Войти</span>
            <ArrowRight size={20} />
          </>
        )}
      </button>
    </form>
  );
};

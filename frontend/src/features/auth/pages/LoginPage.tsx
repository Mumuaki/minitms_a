import React from 'react';
import { LoginForm } from '../components/LoginForm';
import '../styles.css';

export const LoginPage = () => {
  return (
    <div className="auth-page">
      <div className="auth-blob auth-blob-1" />
      <div className="auth-blob auth-blob-2" />
      
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            Mini<span style={{ color: 'var(--color-primary)' }}>TMS</span>
          </div>
          <p className="auth-subtitle">
            Войдите в систему для управления
          </p>
        </div>
        
        <LoginForm />
      </div>
    </div>
  );
};

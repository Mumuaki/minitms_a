import axios from 'axios';

// Используем /api прокси, настроенный в vite.config.ts
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем токен к каждому запросу
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок (например, 401 Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Если токен протух — удаляем его.
      // Логику редиректа лучше обрабатывать в AuthProvider
      localStorage.removeItem('access_token');
    }
    return Promise.reject(error);
  }
);

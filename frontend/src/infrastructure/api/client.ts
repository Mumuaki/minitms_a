import axios from 'axios';

// Same-origin API (host nginx proxies /api/v1). withCredentials is required so the
// httpOnly refresh cookie is sent to POST /auth/refresh (otherwise the browser would
// not include it and the user would be logged out after the 15-minute access token).
export const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = 'Bearer ' + token;
  }
  return config;
});

let refreshing: any = null;

function redirectToLogin() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: any) => {
    const original: any = error.config;
    const status = error.response ? error.response.status : undefined;
    const url: string = original && original.url ? original.url : '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/logout');

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      try {
        if (!refreshing) {
          refreshing = axios
            .post('/api/v1/auth/refresh', {}, { withCredentials: true })
            .then((r) => r.data.access_token)
            .finally(() => {
              refreshing = null;
            });
        }
        const token = await refreshing;
        localStorage.setItem('access_token', token);
        original.headers = original.headers || {};
        original.headers.Authorization = 'Bearer ' + token;
        return apiClient(original);
      } catch (e) {
        redirectToLogin();
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  }
);

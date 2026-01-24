import { apiClient } from '@/infrastructure/api/client';
import { LoginRequest, TokenResponse, UserResponse } from '@/features/auth/types';

export const authService = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    // Backend ожидает x-www-form-urlencoded для OAuth2 формы
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await apiClient.post<TokenResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },

  getMe: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/auth/me');
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

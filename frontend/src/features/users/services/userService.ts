import { apiClient } from '@/infrastructure/api/client';
import { User, CreateUserRequest, UpdateUserRequest } from '../types';

export const userService = {
  getAll: async (): Promise<User[]> => {
    // В реальном API может быть пагинация, пока берем список
    const response = await apiClient.get<User[]>('/users/'); 
    return response.data;
  },

  getById: async (id: number): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${id}`);
    return response.data;
  },

  create: async (data: CreateUserRequest): Promise<User> => {
    const response = await apiClient.post<User>('/users/', data);
    return response.data;
  },

  update: async (id: number, data: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.put<User>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    // В текущем API нет явного удаления, обычно это деактивация, 
    // но если endpoint есть, используем его.
    // Если endpoint нет, можно удалить этот метод или использовать update(is_active=false)
    await apiClient.delete(`/users/${id}`);
  }
};

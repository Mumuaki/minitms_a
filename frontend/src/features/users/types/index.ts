export type UserRole = 'administrator' | 'director' | 'dispatcher' | 'guest';

export interface User {
  id: number;
  email: string;
  username: string; 
  role: UserRole;
  is_active: boolean;
  language?: string;
  created_at?: string;
}

export interface CreateUserRequest {
  email: string;
  username: string;
  password?: string;
  role: UserRole;
  language?: string;
  is_active?: boolean;
}

export interface UpdateUserRequest {
  email?: string;
  username?: string;
  role?: UserRole;
  language?: string;
  is_active?: boolean;
}

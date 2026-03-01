import { apiClient } from './apiClient';
import { 
  setToken, 
  removeToken, 
  setCurrentUser, 
  removeCurrentUser 
} from '../config/api';

// Auth types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role: 'teacher' | 'student';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'teacher' | 'student';
  is_active: boolean;
  created_at: string;
}

// Auth service
class AuthService {
  // Login
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Login failed');
    }

    const data: AuthResponse = await response.json();
    setToken(data.access_token);
    
    // Fetch and store user info
    const user = await this.getMe();
    setCurrentUser(user);
    
    return data;
  }

  // Register
  async register(data: RegisterData): Promise<User> {
    const user = await apiClient.post<User>('/auth/register', data);
    return user;
  }

  // Get current user
  async getMe(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  }

  // Logout
  logout(): void {
    removeToken();
    removeCurrentUser();
  }

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('churgpt_token');
  }
}

export const authService = new AuthService();

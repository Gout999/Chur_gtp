// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  TIMEOUT: 30000,
};

// Get auth token from storage
export const getToken = (): string | null => {
  return localStorage.getItem('churgpt_token');
};

// Set auth token
export const setToken = (token: string): void => {
  localStorage.setItem('churgpt_token', token);
};

// Remove auth token
export const removeToken = (): void => {
  localStorage.removeItem('churgpt_token');
};

// Get current user from storage
export const getCurrentUser = (): any | null => {
  const user = localStorage.getItem('churgpt_user');
  return user ? JSON.parse(user) : null;
};

// Set current user
export const setCurrentUser = (user: any): void => {
  localStorage.setItem('churgpt_user', JSON.stringify(user));
};

// Remove current user
export const removeCurrentUser = (): void => {
  localStorage.removeItem('churgpt_user');
};

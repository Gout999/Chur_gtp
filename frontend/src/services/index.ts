// Export all services
export { apiClient, APIError } from './apiClient';
export { authService, type LoginCredentials, type RegisterData, type User } from './authService';
export { teacherService, type Class, type Material, type Assignment } from './teacherService';
export { studentService, type Mistake, type Submission } from './studentService';
export { chatService, type ChatSession, type ChatMessage } from './chatService';
export { 
  API_CONFIG, 
  getToken, 
  setToken, 
  removeToken, 
  getCurrentUser, 
  setCurrentUser, 
  removeCurrentUser 
} from '../config/api';

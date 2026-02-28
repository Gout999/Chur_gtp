import { apiClient } from './apiClient';

// Chat types
export interface ChatSession {
  id: number;
  user_id: number;
  session_type: string;
  title?: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  session_id?: number;
  context?: Record<string, any>;
}

export interface ChatResponse {
  message: ChatMessage;
  session_id: number;
}

// Chat service
class ChatService {
  // Sessions
  async getSessions(): Promise<ChatSession[]> {
    return apiClient.get<ChatSession[]>('/chat/sessions');
  }

  async createSession(sessionType: string = 'homework', title?: string): Promise<ChatSession> {
    return apiClient.post<ChatSession>('/chat/sessions', {
      session_type: sessionType,
      title,
    });
  }

  async getSession(id: number): Promise<ChatSession> {
    return apiClient.get<ChatSession>(`/chat/sessions/${id}`);
  }

  async updateSession(id: number, title: string): Promise<ChatSession> {
    return apiClient.put<ChatSession>(`/chat/sessions/${id}`, { title });
  }

  async deleteSession(id: number): Promise<void> {
    return apiClient.delete<void>(`/chat/sessions/${id}`);
  }

  // Messages
  async getMessages(sessionId: number): Promise<ChatMessage[]> {
    return apiClient.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
  }

  async sendMessage(message: string, sessionId?: number): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/chat/send', {
      message,
      session_id: sessionId,
    });
  }
}

export const chatService = new ChatService();

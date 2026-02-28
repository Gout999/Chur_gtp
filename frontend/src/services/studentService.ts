import { apiClient } from './apiClient';

// Student types
export interface StudentClass {
  id: number;
  name: string;
  subject: string;
  teacher_id: number;
  schedule?: string;
  color: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface Material {
  id: number;
  title: string;
  subject: string;
  description?: string;
  file_path: string;
  file_type?: string;
  uploaded_by: number;
  class_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface Assignment {
  id: number;
  title: string;
  description?: string;
  class_id: number;
  due_date?: string;
  max_score: number;
  file_path?: string;
  created_at: string;
  updated_at?: string;
}

export interface Submission {
  id: number;
  assignment_id: number;
  student_id: number;
  content?: string;
  file_path?: string;
  score?: number;
  feedback?: string;
  status: 'pending' | 'submitted' | 'graded';
  submitted_at: string;
  graded_at?: string;
}

export interface CreateSubmissionData {
  assignment_id: number;
  content?: string;
}

export interface Mistake {
  id: number;
  student_id: number;
  subject: string;
  topic?: string;
  question: string;
  correct_answer: string;
  student_answer?: string;
  explanation?: string;
  status: 'unresolved' | 'reviewing' | 'resolved';
  created_at: string;
  updated_at?: string;
}

export interface CreateMistakeData {
  subject: string;
  topic?: string;
  question: string;
  correct_answer: string;
  student_answer?: string;
  explanation?: string;
}

export interface MistakeStats {
  total: number;
  unresolved: number;
  reviewing: number;
  resolved: number;
  by_subject: Record<string, number>;
}

export interface StudentStats {
  total_classes: number;
  pending_assignments: number;
  completed_assignments: number;
  total_mistakes: number;
  unresolved_mistakes: number;
}

// Student service
class StudentService {
  // Classes
  async getClasses(): Promise<StudentClass[]> {
    return apiClient.get<StudentClass[]>('/students/classes');
  }

  async getClass(id: number): Promise<StudentClass> {
    return apiClient.get<StudentClass>(`/students/classes/${id}`);
  }

  // Materials
  async getMaterials(subject?: string): Promise<Material[]> {
    const query = subject ? `?subject=${encodeURIComponent(subject)}` : '';
    return apiClient.get<Material[]>(`/students/materials${query}`);
  }

  async getMaterial(id: number): Promise<Material> {
    return apiClient.get<Material>(`/students/materials/${id}`);
  }

  // Assignments
  async getAssignments(status?: string): Promise<Assignment[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient.get<Assignment[]>(`/students/assignments${query}`);
  }

  async getAssignment(id: number): Promise<Assignment> {
    return apiClient.get<Assignment>(`/students/assignments/${id}`);
  }

  // Submissions
  async createSubmission(assignmentId: number, content?: string): Promise<Submission> {
    return apiClient.post<Submission>(`/students/assignments/${assignmentId}/submissions`, {
      content,
    });
  }

  async updateSubmission(assignmentId: number, content?: string): Promise<Submission> {
    return apiClient.put<Submission>(`/students/assignments/${assignmentId}/submissions`, {
      content,
    });
  }

  async getMySubmissions(): Promise<Submission[]> {
    return apiClient.get<Submission[]>('/students/submissions');
  }

  // Mistakes
  async getMistakes(subject?: string, status?: string): Promise<Mistake[]> {
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<Mistake[]>(`/students/mistakes${query}`);
  }

  async getMistake(id: number): Promise<Mistake> {
    return apiClient.get<Mistake>(`/students/mistakes/${id}`);
  }

  async createMistake(data: CreateMistakeData): Promise<Mistake> {
    return apiClient.post<Mistake>('/students/mistakes', data);
  }

  async updateMistake(id: number, data: Partial<CreateMistakeData & { status?: string }>): Promise<Mistake> {
    return apiClient.put<Mistake>(`/students/mistakes/${id}`, data);
  }

  async deleteMistake(id: number): Promise<void> {
    return apiClient.delete<void>(`/students/mistakes/${id}`);
  }

  async getMistakeStats(): Promise<MistakeStats> {
    return apiClient.get<MistakeStats>('/students/mistakes/stats');
  }

  // Dashboard
  async getDashboardStats(): Promise<StudentStats> {
    return apiClient.get<StudentStats>('/students/dashboard/stats');
  }
}

export const studentService = new StudentService();

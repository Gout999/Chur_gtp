import { apiClient } from './apiClient';

// Teacher types
export interface Class {
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

export interface CreateClassData {
  name: string;
  subject: string;
  schedule?: string;
  color?: string;
  description?: string;
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

export interface CreateMaterialData {
  title: string;
  subject: string;
  description?: string;
  class_id?: number;
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

export interface CreateAssignmentData {
  title: string;
  description?: string;
  class_id: number;
  due_date?: string;
  max_score?: number;
}

export interface TeacherStats {
  total_classes: number;
  total_students: number;
  total_materials: number;
  total_assignments: number;
  pending_submissions: number;
}

// Teacher service
class TeacherService {
  // Classes
  async getClasses(): Promise<Class[]> {
    return apiClient.get<Class[]>('/teachers/classes');
  }

  async getClass(id: number): Promise<Class> {
    return apiClient.get<Class>(`/teachers/classes/${id}`);
  }

  async createClass(data: CreateClassData): Promise<Class> {
    return apiClient.post<Class>('/teachers/classes', data);
  }

  async updateClass(id: number, data: Partial<CreateClassData>): Promise<Class> {
    return apiClient.put<Class>(`/teachers/classes/${id}`, data);
  }

  async deleteClass(id: number): Promise<void> {
    return apiClient.delete<void>(`/teachers/classes/${id}`);
  }

  // Enrollments
  async enrollStudent(classId: number, studentId: number): Promise<void> {
    return apiClient.post<void>(`/teachers/classes/${classId}/students/${studentId}`);
  }

  async removeStudent(classId: number, studentId: number): Promise<void> {
    return apiClient.delete<void>(`/teachers/classes/${classId}/students/${studentId}`);
  }

  // Materials
  async getMaterials(): Promise<Material[]> {
    return apiClient.get<Material[]>('/teachers/materials');
  }

  async createMaterial(data: CreateMaterialData): Promise<Material> {
    return apiClient.post<Material>('/teachers/materials', data);
  }

  async updateMaterial(id: number, data: Partial<CreateMaterialData>): Promise<Material> {
    return apiClient.put<Material>(`/teachers/materials/${id}`, data);
  }

  async deleteMaterial(id: number): Promise<void> {
    return apiClient.delete<void>(`/teachers/materials/${id}`);
  }

  // Assignments
  async getAssignments(): Promise<Assignment[]> {
    return apiClient.get<Assignment[]>('/teachers/assignments');
  }

  async createAssignment(data: CreateAssignmentData): Promise<Assignment> {
    return apiClient.post<Assignment>('/teachers/assignments', data);
  }

  async updateAssignment(id: number, data: Partial<CreateAssignmentData>): Promise<Assignment> {
    return apiClient.put<Assignment>(`/teachers/assignments/${id}`, data);
  }

  async deleteAssignment(id: number): Promise<void> {
    return apiClient.delete<void>(`/teachers/assignments/${id}`);
  }

  // Dashboard
  async getDashboardStats(): Promise<TeacherStats> {
    return apiClient.get<TeacherStats>('/teachers/dashboard/stats');
  }
}

export const teacherService = new TeacherService();

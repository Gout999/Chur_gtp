const API_BASE = '/api/v1';
const BEARER_TOKEN = 'dev-token';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers,
      Authorization: `Bearer ${BEARER_TOKEN}`,
    },
  });

  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }

  const json = await res.json();

  if (json && typeof json === 'object' && 'success' in json) {
    if (!json.success) throw new Error(json.error?.detail || 'API error');
    return json.data as T;
  }

  return json as T;
}

/* ============ Teacher - Material Upload ============ */
export interface MaterialUploadResult {
  material_id: string;
  file_name: string;
  file_size: number;
  content_type: string;
  status: string;
  stored_at: string;
}

export async function uploadMaterial(
  file: File,
  teacherId = 'teacher-demo',
  classId?: string,
  subject?: string,
  gradeLevel?: string,
  tags?: string,
  teacherNotes?: string,
): Promise<MaterialUploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('teacher_id', teacherId);
  if (classId) form.append('class_id', classId);
  if (subject) form.append('subject', subject);
  if (gradeLevel) form.append('grade_level', gradeLevel);
  if (tags) form.append('tags', tags);
  if (teacherNotes) form.append('teacher_notes', teacherNotes);

  return request<MaterialUploadResult>('/teacher/materials/upload', {
    method: 'POST',
    body: form,
  });
}

export async function getMaterialStatus(materialId: string) {
  return request<{ material_id: string; status: string; stored_at: string; updated_at: string | null }>(
    `/teacher/materials/${materialId}/status`,
  );
}

/* ============ Teacher - Class Overview & Students ============ */
export interface ClassOverview {
  class_id: string;
  total_students: number;
  total_interactions: number;
  pending_escalations: number;
  at_risk_students: number;
}

export async function getClassOverview(classId: string) {
  return request<ClassOverview>(`/teacher/classes/${classId}/overview`);
}

export interface StudentSummary {
  student_id: string;
  class_id: string | null;
  mastery_score: number;
  latest_topic: string | null;
}

export async function getClassStudents(classId: string) {
  return request<{ class_id: string; students: StudentSummary[] }>(
    `/teacher/classes/${classId}/students`,
  );
}

/* ============ Teacher - Student Detail & Cognition ============ */
export interface StudentDetail {
  student_id: string;
  class_id: string | null;
  profile: Record<string, string>;
  mastery_score: number;
  latest_topic: string | null;
}

export async function getStudentDetail(studentId: string) {
  return request<StudentDetail>(`/teacher/students/${studentId}`);
}

export interface StudentCognition {
  student_id: string;
  mastery_score: number;
  misconceptions: string[];
  confidence: number;
}

export async function getStudentCognition(studentId: string) {
  return request<StudentCognition>(`/teacher/students/${studentId}/cognition`);
}

export async function getStudentAgentLogs(studentId: string) {
  return request<{
    student_id: string;
    logs: { timestamp: string | null; agent: string; decision: string; tool: string | null }[];
  }>(`/teacher/students/${studentId}/agent-logs`);
}

export async function getStudentInteractions(studentId: string, params?: {
  start_date?: string;
  end_date?: string;
  topic?: string;
  limit?: number;
}) {
  const query = new URLSearchParams();
  if (params?.start_date) query.set('start_date', params.start_date);
  if (params?.end_date) query.set('end_date', params.end_date);
  if (params?.topic) query.set('topic', params.topic);
  if (params?.limit) query.set('limit', String(params.limit));
  const qs = query.toString();
  return request<{
    student_id: string;
    total: number;
    items: { timestamp: string | null; topic: string | null; role: string | null; content: string | null }[];
  }>(`/teacher/students/${studentId}/interactions${qs ? '?' + qs : ''}`);
}

/* ============ Teacher - Escalations ============ */
export async function getEscalations() {
  return request<{
    escalations: {
      escalation_id: string;
      student_id: string | null;
      class_id: string | null;
      reason: string | null;
      severity: string | null;
      created_at: string | null;
    }[];
  }>('/teacher/escalations');
}

/* ============ Teacher - Config ============ */
export async function getTeacherConfig(teacherId = 'teacher-demo') {
  return request<{
    teacher_id: string;
    config: Record<string, unknown>;
  }>(`/teacher/config?teacher_id=${teacherId}`);
}

/* ============ Teacher - Lesson Plans ============ */
export interface LessonPlanSection {
  title: string;
  duration_minutes: number;
  activity: string;
  teaching_method: string;
  expected_outcome: string;
}

export interface LessonPlan {
  plan_id: string;
  teacher_id: string;
  class_id: string;
  title: string;
  objective: string;
  material_ids: string[];
  topics: string[];
  sections: LessonPlanSection[];
  version: number;
  updated_at: string;
}

export async function generateLessonPlan(payload: {
  teacher_id: string;
  class_id: string;
  title: string;
  objective: string;
  material_ids?: string[];
  topics?: string[];
}) {
  return request<LessonPlan>('/teacher/lesson-plans/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getLessonPlan(planId: string) {
  return request<LessonPlan>(`/teacher/lesson-plans/${planId}`);
}

/* ============ Teacher - PPT ============ */
export async function generatePpt(planId: string, teacherId = 'teacher-demo', template = 'lesson_default') {
  return request<{ ppt_id: string; status: string; poll_url: string }>(
    `/teacher/lesson-plans/${planId}/ppt`,
    {
      method: 'POST',
      body: JSON.stringify({ teacher_id: teacherId, template }),
    },
  );
}

export async function getPptStatus(pptId: string) {
  return request<{ ppt_id: string; status: string; progress: number }>(
    `/teacher/ppt/${pptId}/status`,
  );
}

export function getPptDownloadUrl(pptId: string) {
  return `${API_BASE}/teacher/ppt/${pptId}/download`;
}

/* ============ Teacher - Messages ============ */
export async function sendMessage(payload: {
  teacher_id: string;
  student_id: string;
  content: string;
  channel?: 'in_app' | 'email' | 'push';
}) {
  return request<{ message_id: string; delivery_state: string; created_at: string }>(
    '/teacher/messages/send',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

export async function getConversation(studentId: string) {
  return request<{
    student_id: string;
    total: number;
    items: {
      message_id: string;
      teacher_id: string;
      student_id: string;
      content: string;
      channel: string;
      created_at: string;
    }[];
  }>(`/teacher/messages/conversations/${studentId}`);
}

/* ============ Teacher - Templates ============ */
export async function getLessonTemplates() {
  return request<{
    templates: { template_id: string; label: string; description: string }[];
  }>('/teacher/lesson-templates');
}

/* ============ Student - Hub ============ */
export async function getStudentHub(studentId: string) {
  return request<Record<string, unknown>>(`/students/${studentId}/hub`);
}

/* ============ Health Check ============ */
export async function healthCheck() {
  const res = await fetch('/health');
  return res.json() as Promise<{ status: string }>;
}

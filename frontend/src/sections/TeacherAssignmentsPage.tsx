import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { PageType } from '@/types';
import { 
  Plus, 
  Users, 
  CheckCircle, 
  Clock,
  FileText,
  Upload,
  Sparkles,
  BarChart3,
  Trash2,
  Edit3,
  Eye,
  ArrowRight,
  BookOpen
} from 'lucide-react';
import './TeacherAssignmentsPage.css';

interface TeacherAssignmentsPageProps {
  onPageChange: (_page: PageType) => void;
}

type AssignmentStatus = 'active' | 'draft' | 'closed';
type SubmissionStatus = 'submitted' | 'graded' | 'late' | 'missing';

interface StudentSubmission {
  id: string;
  studentName: string;
  submittedAt: string;
  status: SubmissionStatus;
  score?: number;
  maxScore: number;
  files: string[];
}

interface Assignment {
  id: string;
  title: string;
  subject: string;
  className: string;
  description: string;
  dueDate: string;
  status: AssignmentStatus;
  maxScore: number;
  submissions: StudentSubmission[];
  createdAt: string;
}

// Mock assignments data for teacher
const mockAssignments: Assignment[] = [
  {
    id: '1',
    title: 'Mathematics Problem Set - Algebra',
    subject: 'Mathematics',
    className: 'Form 3A',
    description: 'Complete problems 1-20 from Chapter 5. Focus on quadratic equations and factoring.',
    dueDate: '2025-03-05',
    status: 'active',
    maxScore: 100,
    createdAt: '2025-02-20',
    submissions: [
      { id: 's1', studentName: 'Alex Chen', submittedAt: '2025-03-04', status: 'submitted', maxScore: 100, files: ['alex_homework.pdf'] },
      { id: 's2', studentName: 'Sarah Kim', submittedAt: '2025-03-03', status: 'graded', score: 85, maxScore: 100, files: ['sarah_homework.pdf'] },
      { id: 's3', studentName: 'James Lee', submittedAt: '2025-03-05', status: 'late', maxScore: 100, files: ['james_homework.pdf'] },
      { id: 's4', studentName: 'Emily Wang', submittedAt: '2025-03-02', status: 'graded', score: 92, maxScore: 100, files: ['emily_homework.pdf'] },
    ]
  },
  {
    id: '2',
    title: 'Science Lab Report',
    subject: 'Science',
    className: 'Form 3A',
    description: 'Write a detailed lab report on the photosynthesis experiment conducted in class.',
    dueDate: '2025-03-03',
    status: 'active',
    maxScore: 100,
    createdAt: '2025-02-18',
    submissions: [
      { id: 's5', studentName: 'Alex Chen', submittedAt: '2025-03-02', status: 'graded', score: 88, maxScore: 100, files: ['alex_lab.pdf'] },
      { id: 's6', studentName: 'Sarah Kim', submittedAt: '2025-03-01', status: 'graded', score: 90, maxScore: 100, files: ['sarah_lab.pdf'] },
    ]
  },
  {
    id: '3',
    title: 'English Essay - Shakespeare Analysis',
    subject: 'English',
    className: 'Form 3B',
    description: 'Write a 500-word essay analyzing the themes in Romeo and Juliet Act 3.',
    dueDate: '2025-02-28',
    status: 'closed',
    maxScore: 100,
    createdAt: '2025-02-15',
    submissions: [
      { id: 's7', studentName: 'James Lee', submittedAt: '2025-02-27', status: 'graded', score: 78, maxScore: 100, files: ['james_essay.pdf'] },
      { id: 's8', studentName: 'Emily Wang', submittedAt: '2025-02-28', status: 'graded', score: 95, maxScore: 100, files: ['emily_essay.pdf'] },
      { id: 's9', studentName: 'Michael Brown', submittedAt: '', status: 'missing', maxScore: 100, files: [] },
    ]
  },
  {
    id: '4',
    title: 'History Quiz Preparation',
    subject: 'History',
    className: 'Form 3A',
    description: 'Study Chapter 7 for upcoming quiz on World War II.',
    dueDate: '2025-03-10',
    status: 'draft',
    maxScore: 50,
    createdAt: '2025-03-01',
    submissions: []
  },
];

const getStatusColor = (status: AssignmentStatus) => {
  switch (status) {
    case 'active': return 'emerald';
    case 'draft': return 'orange';
    case 'closed': return 'gray';
  }
};

const getScoreColor = (score: number, maxScore: number) => {
  const percentage = (score / maxScore) * 100;
  if (percentage >= 90) return '#10b981';
  if (percentage >= 80) return '#3b82f6';
  if (percentage >= 70) return '#f59e0b';
  return '#ef4444';
};

export default function TeacherAssignmentsPage({ onPageChange }: TeacherAssignmentsPageProps) {
  const [filter, setFilter] = useState<AssignmentStatus | 'all'>('all');
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);

  const filteredAssignments = mockAssignments.filter(assignment => {
    const matchesFilter = filter === 'all' || assignment.status === filter;
    return matchesFilter;
  });

  const stats = {
    total: mockAssignments.length,
    active: mockAssignments.filter(a => a.status === 'active').length,
    draft: mockAssignments.filter(a => a.status === 'draft').length,
    closed: mockAssignments.filter(a => a.status === 'closed').length,
  };

  const handleAssignmentClick = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
  };


  if (selectedAssignment) {
    return (
      <AssignmentSubmissions 
        assignment={selectedAssignment}
      />
    );
  }

  return (  // Main assignments list view
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="teacher-assignments-page"
    >
      {/* Hero Section */}
      <div className="teacher-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="hero-content"
        >
          <h1>Assignments Management</h1>
          <p>Create, manage and grade student assignments</p>
        </motion.div>
      </div>

      {/* Stats Section */}
      <section className="stats-section">
        <h2>Overview</h2>
        <div className="stats-grid">
          <motion.div 
            className="stat-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="stat-icon-wrapper gray">
              <FileText size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card emerald"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <div className="stat-icon-wrapper emerald">
              <CheckCircle size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.active}</span>
              <span className="stat-label">Active</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card orange"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="stat-icon-wrapper orange">
              <Clock size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.draft}</span>
              <span className="stat-label">Draft</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card gray"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <div className="stat-icon-wrapper gray">
              <BookOpen size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.closed}</span>
              <span className="stat-label">Closed</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="quick-actions-section">
        <h2>Quick Actions</h2>
        <div className="quick-actions-grid">
          <motion.button
            className="quick-action-card ai"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onClick={() => setShowAIModal(true)}
          >
            <div className="action-icon">
              <Sparkles size={24} />
            </div>
            <div className="action-content">
              <span>AI Generate</span>
              <ArrowRight size={18} />
            </div>
          </motion.button>
          
          <motion.button
            className="quick-action-card create"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            onClick={() => setShowCreateModal(true)}
          >
            <div className="action-icon">
              <Plus size={24} />
            </div>
            <div className="action-content">
              <span>Create Assignment</span>
              <ArrowRight size={18} />
            </div>
          </motion.button>
        </div>
      </section>

      {/* Filter Tabs */}
      <section className="filter-section">
        <div className="filter-tabs">
          {(['all', 'active', 'draft', 'closed'] as const).map((status) => (
            <button
              key={status}
              className={`filter-tab ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </section>

      {/* Assignments List */}
      <section className="assignments-section">
        <h2>All Assignments</h2>
        <div className="assignments-grid">
          {filteredAssignments.length === 0 ? (
            <div className="empty-state">
              <FileText size={48} />
              <p>No assignments found</p>
            </div>
          ) : (
            filteredAssignments.map((assignment, index) => (
              <motion.div
                key={assignment.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index, duration: 0.3 }}
                className={`assignment-row ${getStatusColor(assignment.status)}`}
              >
                <div 
                  className="assignment-main"
                  onClick={() => handleAssignmentClick(assignment)}
                >
                  <div className="assignment-info">
                    <div className="assignment-header-row">
                      <span className="subject-tag">{assignment.subject}</span>
                      <span className={`status-badge ${assignment.status}`}>
                        {assignment.status}
                      </span>
                    </div>
                    <h3>{assignment.title}</h3>
                    <p className="assignment-meta">
                      {assignment.className} • Due {new Date(assignment.dueDate).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <div className="assignment-stats">
                    <div className="stat-item">
                      <Users size={16} />
                      <span>{assignment.submissions.length} submissions</span>
                    </div>
                    <div className="stat-item">
                      <BarChart3 size={16} />
                      <span>
                        {assignment.submissions.filter(s => s.status === 'graded').length} graded
                      </span>
                    </div>
                  </div>
                </div>

                <div className="assignment-actions">
                  <button 
                    className="action-icon-btn view"
                    onClick={() => handleAssignmentClick(assignment)}
                  >
                    <Eye size={18} />
                  </button>
                  <button className="action-icon-btn edit">
                    <Edit3 size={18} />
                  </button>
                  <button className="action-icon-btn delete">
                    <Trash2 size={18} />
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </section>

      {/* Create Assignment Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateAssignmentModal 
            onClose={() => setShowCreateModal(false)}
          />
        )}
      </AnimatePresence>

      {/* AI Generate Modal */}
      <AnimatePresence>
        {showAIModal && (
          <AIGenerateModal
            onClose={() => setShowAIModal(false)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Assignment Submissions Component
// Assignment Submissions Component
interface AssignmentSubmissionsProps {
  assignment: Assignment;
}

function AssignmentSubmissions({ assignment }: AssignmentSubmissionsProps) {
  const [selectedSubmission, setSelectedSubmission] = useState<StudentSubmission | null>(null);
  const [gradeInput, setGradeInput] = useState('');
  const [feedbackInput, setFeedbackInput] = useState('');

  const submissionStats = {
    submitted: assignment.submissions.filter(s => s.status === 'submitted' || s.status === 'late').length,
    graded: assignment.submissions.filter(s => s.status === 'graded').length,
    missing: assignment.submissions.filter(s => s.status === 'missing').length,
    averageScore: assignment.submissions
      .filter(s => s.score !== undefined)
      .reduce((acc, s) => acc + (s.score || 0), 0) / 
      assignment.submissions.filter(s => s.score !== undefined).length || 0,
  };

  const handleGrade = (submission: StudentSubmission) => {
    setSelectedSubmission(submission);
    setGradeInput(submission.score?.toString() || '');
    setFeedbackInput('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="assignment-submissions-page"
    >
      {/* Hero Section */}
      <div className="teacher-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="hero-content"
        >
          <h1>{assignment.title}</h1>
          <p>{assignment.className} • {assignment.subject}</p>
        </motion.div>
      </div>

      {/* Stats Section */}
      <section className="stats-section">
        <h2>Submission Overview</h2>
        <div className="stats-grid">
          <motion.div 
            className="stat-card orange"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="stat-icon-wrapper orange">
              <Clock size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{submissionStats.submitted}</span>
              <span className="stat-label">To Grade</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card emerald"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <div className="stat-icon-wrapper emerald">
              <CheckCircle size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{submissionStats.graded}</span>
              <span className="stat-label">Graded</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card rose"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="stat-icon-wrapper rose">
              <Users size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{submissionStats.missing}</span>
              <span className="stat-label">Missing</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card blue"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <div className="stat-icon-wrapper blue">
              <BarChart3 size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{submissionStats.averageScore.toFixed(0)}%</span>
              <span className="stat-label">Average</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Submissions List */}
      <section className="submissions-section">
        <h2>Student Submissions</h2>
        <div className="submissions-list">
          {assignment.submissions.length === 0 ? (
            <div className="empty-state">
              <Users size={48} />
              <p>No submissions yet</p>
            </div>
          ) : (
            assignment.submissions.map((submission, index) => (
              <motion.div
                key={submission.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index, duration: 0.3 }}
                className={`submission-row ${submission.status}`}
              >
                <div className="submission-info">
                  <h4>{submission.studentName}</h4>
                  <div className="submission-meta">
                    <span className={`submission-status ${submission.status}`}>
                      {submission.status}
                    </span>
                    {submission.submittedAt && (
                      <span className="submission-date">
                        {new Date(submission.submittedAt).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="submission-files">
                  {submission.files.map((file, idx) => (
                    <a key={idx} href="#" className="file-tag">
                      <FileText size={14} />
                      {file}
                    </a>
                  ))}
                </div>

                <div className="submission-grade">
                  {submission.score !== undefined ? (
                    <span 
                      className="grade-badge"
                      style={{ color: getScoreColor(submission.score, submission.maxScore) }}
                    >
                      {submission.score}/{submission.maxScore}
                    </span>
                  ) : (
                    <span className="no-grade">Not graded</span>
                  )}
                </div>

                <button 
                  className="grade-action-btn"
                  onClick={() => handleGrade(submission)}
                >
                  {submission.score !== undefined ? 'Re-grade' : 'Grade'}
                </button>
              </motion.div>
            ))
          )}
        </div>
      </section>

      {/* Grade Modal */}
      <AnimatePresence>
        {selectedSubmission && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            onClick={() => setSelectedSubmission(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="grade-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <h3>Grade: {selectedSubmission.studentName}</h3>
              
              <div className="grade-input-group">
                <label>Score (max {assignment.maxScore})</label>
                <input
                  type="number"
                  value={gradeInput}
                  onChange={(e) => setGradeInput(e.target.value)}
                  max={assignment.maxScore}
                  min={0}
                />
              </div>

              <div className="grade-input-group">
                <label>Feedback</label>
                <textarea
                  value={feedbackInput}
                  onChange={(e) => setFeedbackInput(e.target.value)}
                  placeholder="Enter feedback for student..."
                  rows={4}
                />
              </div>

              <div className="modal-actions">
                <button 
                  className="cancel-btn"
                  onClick={() => setSelectedSubmission(null)}
                >
                  Cancel
                </button>
                <button className="save-btn">
                  Save Grade
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Create Assignment Modal
interface CreateAssignmentModalProps {
  onClose: () => void;
}

function CreateAssignmentModal({ onClose }: CreateAssignmentModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="modal-overlay"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="create-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Create New Assignment</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Assignment Title</label>
            <input type="text" placeholder="Enter assignment title" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Subject</label>
              <select>
                <option>Mathematics</option>
                <option>Science</option>
                <option>English</option>
                <option>History</option>
              </select>
            </div>

            <div className="form-group">
              <label>Class</label>
              <select>
                <option>Form 3A</option>
                <option>Form 3B</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea placeholder="Enter assignment description" rows={4} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Due Date</label>
              <input type="date" />
            </div>

            <div className="form-group">
              <label>Max Score</label>
              <input type="number" defaultValue={100} />
            </div>
          </div>

          <div className="form-group">
            <label>Attachments</label>
            <div className="upload-area">
              <Upload size={24} />
              <span>Drag files here or click to upload</span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button className="create-btn">Create Assignment</button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// AI Generate Modal
interface AIGenerateModalProps {
  onClose: () => void;
}

function AIGenerateModal({ onClose }: AIGenerateModalProps) {
  const [step, setStep] = useState(1);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="modal-overlay"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="ai-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>
            <Sparkles size={20} />
            AI Assignment Generator
          </h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {step === 1 && (
            <>
              <p className="ai-description">
                Upload curriculum documents and let AI generate relevant assignments with questions and knowledge points.
              </p>

              <div className="upload-area large">
                <Upload size={32} />
                <span>Upload PDF, DOCX, or TXT files</span>
                <p className="upload-hint">Our AI will analyze the content and generate appropriate questions</p>
              </div>

              <div className="form-group">
                <label>Or paste content directly</label>
                <textarea 
                  placeholder="Paste your curriculum content here..."
                  rows={6}
                />
              </div>
            </>
          )}

          {step === 2 && (
            <div className="ai-generating">
              <div className="spinner"></div>
              <p>AI is analyzing your content...</p>
              <p className="hint">This may take a few moments</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button 
            className="generate-btn"
            onClick={() => setStep(2)}
          >
            <Sparkles size={16} />
            Generate with AI
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { PageType } from '@/types';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Upload,
  BookOpen,
  ArrowRight
} from 'lucide-react';
import './AssignmentsPage.css';

interface AssignmentsPageProps {
  onPageChange: (page: PageType) => void;
}

type AssignmentStatus = 'pending' | 'submitted' | 'graded' | 'overdue';
type AssignmentType = 'homework' | 'quiz' | 'project' | 'exam';

interface Assignment {
  id: string;
  title: string;
  subject: string;
  type: AssignmentType;
  description: string;
  dueDate: string;
  status: AssignmentStatus;
  score?: number;
  maxScore: number;
  attachments?: string[];
  submittedAt?: string;
  feedback?: string;
}

// Mock assignments data
const mockAssignments: Assignment[] = [
  {
    id: '1',
    title: 'Mathematics Problem Set - Algebra',
    subject: 'Mathematics',
    type: 'homework',
    description: 'Complete problems 1-20 from Chapter 5. Focus on quadratic equations and factoring.',
    dueDate: '2025-03-05',
    status: 'pending',
    maxScore: 100,
    attachments: ['algebra_worksheet.pdf']
  },
  {
    id: '2',
    title: 'Science Lab Report',
    subject: 'Science',
    type: 'project',
    description: 'Write a detailed lab report on the photosynthesis experiment conducted in class.',
    dueDate: '2025-03-03',
    status: 'submitted',
    maxScore: 100,
    submittedAt: '2025-03-02',
    attachments: ['lab_report_template.docx']
  },
  {
    id: '3',
    title: 'English Essay - Shakespeare Analysis',
    subject: 'English',
    type: 'homework',
    description: 'Write a 500-word essay analyzing the themes in Romeo and Juliet Act 3.',
    dueDate: '2025-02-28',
    status: 'graded',
    maxScore: 100,
    score: 85,
    submittedAt: '2025-02-27',
    feedback: 'Good analysis of themes. Work on grammar and sentence structure.'
  },
  {
    id: '4',
    title: 'History Quiz - World War II',
    subject: 'History',
    type: 'quiz',
    description: '20 multiple choice questions covering key events of WWII.',
    dueDate: '2025-02-25',
    status: 'overdue',
    maxScore: 50,
  },
  {
    id: '5',
    title: 'Art Project - Portrait Drawing',
    subject: 'Art',
    type: 'project',
    description: 'Create a portrait using charcoal or pencil. Focus on shading and proportions.',
    dueDate: '2025-03-10',
    status: 'pending',
    maxScore: 100,
  },
  {
    id: '6',
    title: 'Physics Problem Set - Mechanics',
    subject: 'Physics',
    type: 'homework',
    description: 'Solve problems related to Newton\'s laws and motion.',
    dueDate: '2025-03-01',
    status: 'graded',
    maxScore: 100,
    score: 92,
    submittedAt: '2025-02-28',
    feedback: 'Excellent work! Very detailed solutions.'
  },
];

const getStatusIcon = (status: AssignmentStatus) => {
  switch (status) {
    case 'pending':
      return <Clock size={24} />;
    case 'submitted':
      return <CheckCircle size={24} />;
    case 'graded':
      return <CheckCircle size={24} />;
    case 'overdue':
      return <AlertCircle size={24} />;
  }
};

const getStatusColor = (status: AssignmentStatus) => {
  switch (status) {
    case 'pending':
      return 'orange';
    case 'submitted':
      return 'blue';
    case 'graded':
      return 'emerald';
    case 'overdue':
      return 'rose';
  }
};

const getTypeLabel = (type: AssignmentType) => {
  switch (type) {
    case 'homework':
      return 'Homework';
    case 'quiz':
      return 'Quiz';
    case 'project':
      return 'Project';
    case 'exam':
      return 'Exam';
  }
};

const getScoreColor = (score: number, maxScore: number) => {
  const percentage = (score / maxScore) * 100;
  if (percentage >= 90) return '#10b981';
  if (percentage >= 80) return '#3b82f6';
  if (percentage >= 70) return '#f59e0b';
  return '#ef4444';
};

export default function AssignmentsPage({ onPageChange }: AssignmentsPageProps) {
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);

  const stats = {
    total: mockAssignments.length,
    pending: mockAssignments.filter(a => a.status === 'pending').length,
    submitted: mockAssignments.filter(a => a.status === 'submitted').length,
    graded: mockAssignments.filter(a => a.status === 'graded').length,
  };

  const handleAssignmentClick = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
  };

  const handleBack = () => {
    if (selectedAssignment) {
      setSelectedAssignment(null);
    } else {
      onPageChange('dashboard');
    }
  };

  if (selectedAssignment) {
    return (
      <AssignmentDetail 
        assignment={selectedAssignment} 
        onBack={handleBack}
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="assignments-page"
    >
      {/* Hero Section */}
      {/* Hero Section */}
      <div className="assignments-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="hero-content"
        >
          <h1>My Assignments</h1>
          <p>View and manage all your assignments</p>
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
            className="stat-card orange"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <div className="stat-icon-wrapper orange">
              <Clock size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.pending}</span>
              <span className="stat-label">Pending</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card blue"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="stat-icon-wrapper blue">
              <CheckCircle size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.submitted}</span>
              <span className="stat-label">Submitted</span>
            </div>
          </motion.div>
          
          <motion.div 
            className="stat-card emerald"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <div className="stat-icon-wrapper emerald">
              <BookOpen size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats.graded}</span>
              <span className="stat-label">Graded</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Assignments List */}
      <section className="assignments-section">
        <h2>All Assignments</h2>
        <div className="assignments-grid">
          {mockAssignments.map((assignment, index) => (
            <motion.div
              key={assignment.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index, duration: 0.4 }}
              className={`assignment-card ${getStatusColor(assignment.status)}`}
              onClick={() => handleAssignmentClick(assignment)}
            >
              <div className="assignment-icon">
                {getStatusIcon(assignment.status)}
              </div>
              
              <div className="assignment-content">
                <div className="assignment-header">
                  <span className="subject-tag">{assignment.subject}</span>
                  <span className={`status-badge ${assignment.status}`}>
                    {assignment.status}
                  </span>
                </div>
                <h3>{assignment.title}</h3>
                <p className="assignment-meta">
                  {getTypeLabel(assignment.type)} • Due {new Date(assignment.dueDate).toLocaleDateString()}
                </p>
              </div>
              
              <div className="assignment-action">
                {assignment.score !== undefined ? (
                  <div 
                    className="score-display"
                    style={{ color: getScoreColor(assignment.score, assignment.maxScore) }}
                  >
                    <span className="score-value">{assignment.score}</span>
                    <span className="score-divider">/</span>
                    <span className="score-max">{assignment.maxScore}</span>
                  </div>
                ) : (
                  <div className="max-score">
                    <span>{assignment.maxScore} pts</span>
                  </div>
                )}
                <ArrowRight size={18} className="arrow-icon" />
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </motion.div>
  );
}

// Assignment Detail Component
interface AssignmentDetailProps {
  assignment: Assignment;
  onBack: () => void;
}

function AssignmentDetail({ assignment, onBack }: AssignmentDetailProps) {
  const [file, setFile] = useState<File | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };


  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="assignment-detail-page"
    >
      {/* Hero Section */}
      {/* Hero Section */}
      <div className="assignments-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="hero-content"
        >
          <h1>Assignment Details</h1>
          <p>View details and submit your work</p>
        </motion.div>
      </div>

      <div className="detail-container">
        {/* Main Info Card */}
        <motion.div 
          className="detail-main-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className={`detail-header-badge ${assignment.status}`}>
            {getStatusIcon(assignment.status)}
            <span>{assignment.status.charAt(0).toUpperCase() + assignment.status.slice(1)}</span>
          </div>

          <h2>{assignment.title}</h2>

          <div className="detail-tags">
            <span className="detail-subject">{assignment.subject}</span>
            <span className="detail-type">{getTypeLabel(assignment.type)}</span>
          </div>

          <div className="detail-section">
            <h3>Description</h3>
            <p>{assignment.description}</p>
          </div>

          {assignment.attachments && assignment.attachments.length > 0 && (
            <div className="detail-section">
              <h3>Attachments</h3>
              <div className="attachments-list">
                {assignment.attachments.map((attachment, idx) => (
                  <a key={idx} href="#" className="attachment-item">
                    <FileText size={18} />
                    {attachment}
                  </a>
                ))}
              </div>
            </div>
          )}

          {assignment.feedback && (
            <div className="detail-section feedback">
              <h3>Teacher Feedback</h3>
              <div className="feedback-box">
                <p>{assignment.feedback}</p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Sidebar Info */}
        <motion.div 
          className="detail-sidebar"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="info-box">
            <h3>Assignment Info</h3>
            
            <div className="info-row">
              <span className="info-label">Due Date</span>
              <span className="info-value">
                {new Date(assignment.dueDate).toLocaleDateString('en-US', {
                  weekday: 'short',
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                })}
              </span>
            </div>

            <div className="info-row">
              <span className="info-label">Max Score</span>
              <span className="info-value">{assignment.maxScore} points</span>
            </div>

            {assignment.submittedAt && (
              <div className="info-row">
                <span className="info-label">Submitted</span>
                <span className="info-value">
                  {new Date(assignment.submittedAt).toLocaleDateString()}
                </span>
              </div>
            )}

            {assignment.score !== undefined && (
              <div className="info-row score-row">
                <span className="info-label">Your Score</span>
                <span 
                  className="score-large"
                  style={{ color: getScoreColor(assignment.score, assignment.maxScore) }}
                >
                  {assignment.score}/{assignment.maxScore}
                </span>
              </div>
            )}
          </div>

          {assignment.status === 'pending' && (
            <div className="submit-box">
              <h3>Submit Assignment</h3>
              
              <div className="upload-wrapper">
                <input
                  type="file"
                  id="assignment-upload"
                  onChange={handleFileUpload}
                  className="hidden-input"
                />
                <label htmlFor="assignment-upload" className="upload-btn">
                  <Upload size={20} />
                  <span>{file ? file.name : 'Choose file'}</span>
                </label>
              </div>

              <button 
                className="submit-action-btn"
                disabled={!file}
              >
                Submit Assignment
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}

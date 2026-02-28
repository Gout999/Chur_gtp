import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { PageType } from '@/types';
import { TrendingUp, TrendingDown, Award, BookOpen, Target, Hexagon } from 'lucide-react';
import './TeacherAnalytics.css';

interface TeacherAnalyticsProps {
  onPageChange: (_page: PageType) => void;
}

// Mock data for analytics
const mockData = {
  stats: {
    classAverageScore: '78%',
    passRate: '92%',
    topPerformingSubject: 'Mathematics'
  },
  students: [
    { id: 1, name: 'Alex Chen', overallScore: 85, performance: 'Excellent' },
    { id: 2, name: 'Sarah Kim', overallScore: 78, performance: 'Good' },
    { id: 3, name: 'James Lee', overallScore: 72, performance: 'Average' },
    { id: 4, name: 'Emily Wang', overallScore: 88, performance: 'Excellent' },
    { id: 5, name: 'Michael Brown', overallScore: 68, performance: 'Average' },
  ],
  subjectStrengths: [
    { subject: 'Math', value: 85 },
    { subject: 'Science', value: 78 },
    { subject: 'English', value: 72 },
    { subject: 'History', value: 68 },
    { subject: 'Art', value: 90 },
    { subject: 'PE', value: 82 },
  ],
  knowledgeGaps: [
    { topic: 'Algebra Basics', difficulty: 'High', studentsAtRisk: 8 },
    { topic: 'Reading Comprehension', difficulty: 'Medium', studentsAtRisk: 5 },
    { topic: 'Scientific Method', difficulty: 'Low', studentsAtRisk: 3 },
  ]
};

type TransitionPhase = 'idle' | 'expand' | 'slideDown' | 'complete';
type ViewMode = 'overview' | 'student-detail';

interface SubjectScore {
  subject: string;
  score: number;
  fullMark: number;
}

const detailedStudentData: Record<number, {
  strengths: string[];
  weaknesses: string[];
  recentScores: { subject: string; score: number; date: string }[];
  subjectScores: SubjectScore[];
  recommendations: string[];
}> = {
  1: {
    strengths: ['Mathematics', 'Problem Solving', 'Critical Thinking'],
    weaknesses: ['Essay Writing', 'Time Management'],
    recentScores: [
      { subject: 'Math', score: 92, date: '2025-02-20' },
      { subject: 'Science', score: 85, date: '2025-02-18' },
      { subject: 'English', score: 78, date: '2025-02-15' },
    ],
    subjectScores: [
      { subject: 'Math', score: 92, fullMark: 100 },
      { subject: 'Science', score: 85, fullMark: 100 },
      { subject: 'English', score: 78, fullMark: 100 },
      { subject: 'History', score: 82, fullMark: 100 },
      { subject: 'Chinese', score: 88, fullMark: 100 },
      { subject: 'Physics', score: 90, fullMark: 100 },
    ],
    recommendations: [
      'Practice essay writing weekly',
      'Use timer for homework assignments',
      'Join debate club to improve communication',
    ],
  },
  2: {
    strengths: ['English Literature', 'Creative Writing', 'Public Speaking'],
    weaknesses: ['Mathematics', 'Physics'],
    recentScores: [
      { subject: 'English', score: 88, date: '2025-02-21' },
      { subject: 'History', score: 82, date: '2025-02-19' },
      { subject: 'Math', score: 72, date: '2025-02-16' },
    ],
    subjectScores: [
      { subject: 'Math', score: 72, fullMark: 100 },
      { subject: 'Science', score: 75, fullMark: 100 },
      { subject: 'English', score: 88, fullMark: 100 },
      { subject: 'History', score: 82, fullMark: 100 },
      { subject: 'Chinese', score: 85, fullMark: 100 },
      { subject: 'Physics', score: 68, fullMark: 100 },
    ],
    recommendations: [
      'Attend math tutoring twice a week',
      'Form study group for physics',
      'Use visual aids for math concepts',
    ],
  },
  3: {
    strengths: ['Science', 'Biology', 'Research Skills'],
    weaknesses: ['Foreign Language', 'Art History'],
    recentScores: [
      { subject: 'Science', score: 82, date: '2025-02-22' },
      { subject: 'Biology', score: 86, date: '2025-02-17' },
      { subject: 'Spanish', score: 68, date: '2025-02-14' },
    ],
    subjectScores: [
      { subject: 'Math', score: 75, fullMark: 100 },
      { subject: 'Science', score: 82, fullMark: 100 },
      { subject: 'English', score: 70, fullMark: 100 },
      { subject: 'History', score: 72, fullMark: 100 },
      { subject: 'Chinese', score: 74, fullMark: 100 },
      { subject: 'Physics', score: 80, fullMark: 100 },
    ],
    recommendations: [
      'Practice Spanish with language app daily',
      'Use flashcards for art history dates',
      'Participate in science fair',
    ],
  },
  4: {
    strengths: ['Art', 'Design', 'Visual Communication'],
    weaknesses: ['Mathematics', 'Chemistry'],
    recentScores: [
      { subject: 'Art', score: 95, date: '2025-02-23' },
      { subject: 'Design', score: 92, date: '2025-02-20' },
      { subject: 'Chemistry', score: 75, date: '2025-02-18' },
    ],
    subjectScores: [
      { subject: 'Math', score: 70, fullMark: 100 },
      { subject: 'Science', score: 75, fullMark: 100 },
      { subject: 'English', score: 85, fullMark: 100 },
      { subject: 'History', score: 88, fullMark: 100 },
      { subject: 'Chinese', score: 90, fullMark: 100 },
      { subject: 'Physics', score: 72, fullMark: 100 },
    ],
    recommendations: [
      'Get chemistry tutor for lab work',
      'Use art skills to visualize math problems',
      'Join art club for portfolio development',
    ],
  },
  5: {
    strengths: ['Physical Education', 'Teamwork', 'Leadership'],
    weaknesses: ['Academic Writing', 'Research Methods'],
    recentScores: [
      { subject: 'PE', score: 90, date: '2025-02-21' },
      { subject: 'History', score: 72, date: '2025-02-19' },
      { subject: 'English', score: 70, date: '2025-02-16' },
    ],
    subjectScores: [
      { subject: 'Math', score: 65, fullMark: 100 },
      { subject: 'Science', score: 68, fullMark: 100 },
      { subject: 'English', score: 70, fullMark: 100 },
      { subject: 'History', score: 72, fullMark: 100 },
      { subject: 'Chinese', score: 74, fullMark: 100 },
      { subject: 'Physics', score: 66, fullMark: 100 },
    ],
    recommendations: [
      'Visit writing center for essay help',
      'Read academic articles weekly',
      'Use leadership skills in study groups',
    ],
  },
};

// Radar Chart Component
function RadarChart({ data, size = 280 }: { data: SubjectScore[]; size?: number }) {
  const center = size / 2;
  const radius = size * 0.35;
  const angleStep = (Math.PI * 2) / data.length;
  
  const getPoint = (index: number, score: number) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (score / 100) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };
  
  const gridLevels = [20, 40, 60, 80, 100];
  
  const polygonPoints = data.map((d, i) => {
    const point = getPoint(i, d.score);
    return `${point.x},${point.y}`;
  }).join(' ');
  
  return (
    <svg width={size} height={size} className="radar-chart">
      {/* Grid */}
      {gridLevels.map((level) => {
        const levelRadius = (level / 100) * radius;
        const points = data.map((_, i) => {
          const angle = i * angleStep - Math.PI / 2;
          return `${center + levelRadius * Math.cos(angle)},${center + levelRadius * Math.sin(angle)}`;
        }).join(' ');
        
        return (
          <polygon
            key={level}
            points={points}
            fill="none"
            stroke="rgba(255,255,255,0.15)"
            strokeWidth="1"
          />
        );
      })}
      
      {/* Axes */}
      {data.map((_, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const x2 = center + radius * Math.cos(angle);
        const y2 = center + radius * Math.sin(angle);
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x2}
            y2={y2}
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="1"
          />
        );
      })}
      
      {/* Data Area */}
      <polygon
        points={polygonPoints}
        fill="rgba(99, 102, 241, 0.4)"
        stroke="#818cf8"
        strokeWidth="2"
      />
      
      {/* Data Points */}
      {data.map((d, i) => {
        const point = getPoint(i, d.score);
        return (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r="4"
            fill="#818cf8"
            stroke="white"
            strokeWidth="2"
          />
        );
      })}
      
      {/* Labels */}
      {data.map((d, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const labelRadius = radius + 25;
        const x = center + labelRadius * Math.cos(angle);
        const y = center + labelRadius * Math.sin(angle);
        return (
          <text
            key={i}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="rgba(255,255,255,0.8)"
            fontSize="11"
            fontWeight="500"
          >
            {d.subject}
          </text>
        );
      })}
    </svg>
  );
}

// Student Detail View Component
interface StudentDetailViewProps {
  student: typeof mockData.students[0];
  details: {
    strengths: string[];
    weaknesses: string[];
    recentScores: { subject: string; score: number; date: string }[];
    subjectScores: SubjectScore[];
    recommendations: string[];
  } | null;
  onBack: () => void;
}

function StudentDetailView({ student, details, onBack }: StudentDetailViewProps) {
  if (!details) return null;

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#4caf50';
    if (score >= 80) return '#2196f3';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  return (
    <motion.div
      key="student-detail"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="student-detail-view"
    >
      {/* Back Button - Top Left */}
      <button
        onClick={onBack}
        className="back-to-overview-btn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5" />
          <path d="M12 19l-7-7 7-7" />
        </svg>
        Back to Overview
      </button>

      {/* Student Header */}
      <header className="student-detail-header">
        <div className="student-avatar">
          {student.name.charAt(0)}
        </div>
        <div className="student-title">
          <h1>{student.name}</h1>
          <div className="student-meta">
            <span className="score-badge">Overall: {student.overallScore}%</span>
            <span className={`performance-badge ${student.performance.toLowerCase()}`}>
              {student.performance}
            </span>
          </div>
        </div>
      </header>

      {/* Two Column Layout */}
      <div className="student-detail-grid">
        {/* Left Column */}
        <div className="detail-column">
          <section className="detail-section radar-section">
            <h3><Hexagon size={18} /> Subject Performance Analysis</h3>
            <div className="radar-container">
              <RadarChart data={details.subjectScores} size={300} />
            </div>
            <div className="radar-legend">
              {details.subjectScores.map((subject) => (
                <div key={subject.subject} className="legend-item">
                  <span 
                    className="legend-color" 
                    style={{ backgroundColor: getScoreColor(subject.score) }}
                  />
                  <span className="legend-subject">{subject.subject}</span>
                  <span className="legend-score">{subject.score}%</span>
                </div>
              ))}
            </div>
          </section>

          <section className="detail-section">
            <h3><TrendingUp size={18} /> Strengths</h3>
            <div className="tags-container">
              {details.strengths.map((strength, idx) => (
                <span key={idx} className="tag strength-tag">{strength}</span>
              ))}
            </div>
          </section>

          <section className="detail-section">
            <h3><TrendingDown size={18} /> Areas for Improvement</h3>
            <div className="tags-container">
              {details.weaknesses.map((weakness, idx) => (
                <span key={idx} className="tag weakness-tag">{weakness}</span>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column */}
        <div className="detail-column">
          <section className="detail-section">
            <h3><BookOpen size={18} /> Recent Scores</h3>
            <div className="scores-list">
              {details.recentScores.map((score, idx) => (
                <div key={idx} className="score-item">
                  <div className="score-info">
                    <span className="score-subject">{score.subject}</span>
                    <span className="score-date">{score.date}</span>
                  </div>
                  <span 
                    className="score-value"
                    style={{ color: getScoreColor(score.score) }}
                  >
                    {score.score}%
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="detail-section">
            <h3><Target size={18} /> Personalized Recommendations</h3>
            <ul className="recommendations-list">
              {details.recommendations.map((rec, idx) => (
                <li key={idx} className="recommendation-item">
                  <Award size={16} />
                  {rec}
                </li>
              ))}
            </ul>
          </section>

          <section className="detail-section">
            <h3>Quick Actions</h3>
            <div className="quick-actions">
              <button className="action-btn primary">Generate Report</button>
              <button className="action-btn">Schedule Meeting</button>
              <button className="action-btn">Send Message</button>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}

export default function TeacherAnalytics({ onPageChange }: TeacherAnalyticsProps) {
  const [scale, setScale] = useState(0);
  const [contentOpacity, setContentOpacity] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [selectedStudent, setSelectedStudent] = useState<typeof mockData.students[0] | null>(null);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const phaseRef = useRef<TransitionPhase>('idle');

  useEffect(() => {
    phaseRef.current = 'expand';
    startTimeRef.current = performance.now();

    const animate = (time: number) => {
      const currentPhase = phaseRef.current;
      
      if (currentPhase === 'expand') {
        const elapsed = time - (startTimeRef.current || time);
        const progress = Math.min(elapsed / 1200, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        setScale(easeOut);
        
        if (progress >= 1) {
          phaseRef.current = 'slideDown';
          startTimeRef.current = time;
        }
      } else if (currentPhase === 'slideDown') {
        const elapsed = time - (startTimeRef.current || time);
        const progress = Math.min(elapsed / 800, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        setContentOpacity(easeOut);
        
        if (progress >= 1) {
          phaseRef.current = 'complete';
          setShowContent(true);
        }
      }
      
      if (phaseRef.current !== 'complete') {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const handleStudentClick = (student: typeof mockData.students[0]) => {
    setSelectedStudent(student);
    setViewMode('student-detail');
  };

  const getStudentDetails = (studentId: number) => {
    return detailedStudentData[studentId] || null;
  };

  const handleBackToOverview = () => {
    setViewMode('overview');
    setSelectedStudent(null);
  };

  return (
    <div className="teacher-analytics">
      {/* Expanding Background */}
      <div 
        className="analytics-bg"
        style={{ 
          transform: `scale(${scale})`,
          opacity: Math.min(scale * 2, 1)
        }}
      >
        <img src="/images/teacher-analytics-bg.jpg" alt="Analytics" />
        <div className="analytics-bg-overlay" />
      </div>

      {/* Content */}
      <motion.div 
        className="analytics-content"
        initial={{ y: 50, opacity: 0 }}
        animate={{
          y: showContent ? 0 : 50,
          opacity: contentOpacity
        }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      >
        <AnimatePresence mode="wait">
          {viewMode === 'overview' ? (
            <motion.div
              key="overview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Header */}
              <header className="analytics-header">
                <h1>Analytics Dashboard</h1>
                <p>Student performance insights and analytics</p>
              </header>

              {/* Stats Cards */}
              <section className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">📊</div>
                  <div className="stat-info">
                    <span className="stat-label">Class Average Score</span>
                    <span className="stat-value">{mockData.stats.classAverageScore}</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">✅</div>
                  <div className="stat-info">
                    <span className="stat-label">Pass Rate</span>
                    <span className="stat-value">{mockData.stats.passRate}</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">🏆</div>
                  <div className="stat-info">
                    <span className="stat-label">Top Subject</span>
                    <span className="stat-value">{mockData.stats.topPerformingSubject}</span>
                  </div>
                </div>
              </section>

              {/* Student Table */}
              <section className="students-section">
                <h2>Student Performance <span className="subtitle">(Click a student to view details)</span></h2>
                <table className="students-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Overall Score</th>
                      <th>Performance</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockData.students.map((student) => (
                      <tr 
                        key={student.id} 
                        onClick={() => handleStudentClick(student)}
                        className="clickable-row"
                      >
                        <td>{student.name}</td>
                        <td>{student.overallScore}%</td>
                        <td>
                          <span className={`performance-badge ${student.performance.toLowerCase()}`}>
                            {student.performance}
                          </span>
                        </td>
                        <td>
                          <button className="view-details-btn">View Details →</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

              {/* Subject Strengths */}
              <section className="subjects-section">
                <h2>Subject Strengths</h2>
                <div className="subject-bars">
                  {mockData.subjectStrengths.map((subject) => (
                    <div key={subject.subject} className="subject-bar">
                      <span className="subject-name">{subject.subject}</span>
                      <div className="bar-container">
                        <div 
                          className="bar-fill" 
                          style={{ width: `${subject.value}%` }}
                        />
                      </div>
                      <span className="subject-value">{subject.value}%</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* Knowledge Gaps */}
              <section className="gaps-section">
                <h2>Knowledge Gaps</h2>
                <div className="gaps-list">
                  {mockData.knowledgeGaps.map((gap) => (
                    <div key={gap.topic} className="gap-item">
                      <span className="gap-topic">{gap.topic}</span>
                      <span className={`gap-difficulty ${gap.difficulty.toLowerCase()}`}>
                        {gap.difficulty}
                      </span>
                      <span className="gap-students">{gap.studentsAtRisk} students at risk</span>
                    </div>
                  ))}
                </div>
              </section>
            </motion.div>
          ) : (
            selectedStudent && (
              <StudentDetailView 
                student={selectedStudent}
                details={getStudentDetails(selectedStudent.id)}
                onBack={handleBackToOverview}
              />
            )
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

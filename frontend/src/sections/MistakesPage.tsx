import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, BookOpen, Target, Award, Calculator, FlaskConical, BookText, Clock } from 'lucide-react';
import type { PageType } from '@/types';
import './MistakesPage.css';

interface MistakesPageProps {
  onPageChange: (_page: PageType) => void;
}

const subjectIcons: Record<string, React.ElementType> = {
  Mathematics: Calculator,
  Science: FlaskConical,
  English: BookText,
  History: Clock,
};

const mistakeCategories = [
  {
    subject: 'Mathematics',
    mistakes: 12,
    corrected: 8,
    color: 'blue',
    topics: ['Algebra', 'Geometry', 'Calculus']
  },
  {
    subject: 'Science',
    mistakes: 7,
    corrected: 5,
    color: 'emerald',
    topics: ['Biology', 'Chemistry', 'Physics']
  },
  {
    subject: 'English',
    mistakes: 5,
    corrected: 3,
    color: 'orange',
    topics: ['Grammar', 'Literature', 'Writing']
  },
  {
    subject: 'History',
    mistakes: 4,
    corrected: 4,
    color: 'rose',
    topics: ['World History', 'Local History']
  },
];

const recentMistakes = [
  {
    id: 1,
    question: 'Solve for x: 2x² + 5x - 3 = 0',
    yourAnswer: 'x = 1, x = -3',
    correctAnswer: 'x = 0.5, x = -3',
    subject: 'Mathematics',
    date: '2025-02-28',
    status: 'reviewed'
  },
  {
    id: 2,
    question: 'What is the powerhouse of the cell?',
    yourAnswer: 'Nucleus',
    correctAnswer: 'Mitochondria',
    subject: 'Science',
    date: '2025-02-27',
    status: 'reviewed'
  },
  {
    id: 3,
    question: 'Explain the process of photosynthesis',
    yourAnswer: 'Plants absorb sunlight...',
    correctAnswer: 'Plants convert light energy...',
    subject: 'Science',
    date: '2025-02-26',
    status: 'pending'
  },
];

export default function MistakesPage({ onPageChange }: MistakesPageProps) {
  const totalMistakes = mistakeCategories.reduce((sum, cat) => sum + cat.mistakes, 0);
  const totalCorrected = mistakeCategories.reduce((sum, cat) => sum + cat.corrected, 0);
  const progressPercentage = Math.round((totalCorrected / totalMistakes) * 100);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="mistakes-page"
    >
      <main className="page-content">
        {/* Hero Progress Section */}
        <section className="hero-section">
          <motion.div 
            className="progress-hero"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="progress-ring-container">
              <div className="progress-ring">
                <svg viewBox="0 0 120 120" className="ring-svg">
                  <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#34d399" />
                    </linearGradient>
                  </defs>
                  <circle className="ring-bg" cx="60" cy="60" r="54" />
                  <circle 
                    className="ring-fill" 
                    cx="60" 
                    cy="60" 
                    r="54" 
                    style={{ 
                      strokeDasharray: `${progressPercentage * 3.39} 339`,
                    }}
                  />
                </svg>
                <div className="ring-content">
                  <span className="ring-percentage">{progressPercentage}%</span>
                  <span className="ring-label">Corrected</span>
                </div>
              </div>
            </div>

            <div className="progress-stats">
              <div className="stat-item">
                <div className="stat-icon total">
                  <Target size={20} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">{totalMistakes}</span>
                  <span className="stat-label">Total Mistakes</span>
                </div>
              </div>

              <div className="stat-item">
                <div className="stat-icon corrected">
                  <CheckCircle size={20} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">{totalCorrected}</span>
                  <span className="stat-label">Corrected</span>
                </div>
              </div>

              <div className="stat-item">
                <div className="stat-icon streak">
                  <Award size={20} />
                </div>
                <div className="stat-info">
                  <span className="stat-value">5</span>
                  <span className="stat-label">Day Streak</span>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Subject Stats Grid */}
        <section className="subjects-section">
          <div className="section-header">
            <h2 className="section-title">By Subject</h2>
            <p className="section-subtitle">Track your progress across different subjects</p>
          </div>
          
          <div className="subjects-grid">
            {mistakeCategories.map((category, index) => {
              const SubjectIcon = subjectIcons[category.subject] || BookOpen;
              return (
                <motion.div
                  key={category.subject}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + index * 0.05 }}
                  className={`subject-card ${category.color}`}
                >
                  <div className="card-top">
                    <div className="subject-icon">
                      <SubjectIcon size={24} />
                    </div>
                    <div className="mistake-badge">
                      <span className="corrected-count">{category.corrected}</span>
                      <span className="divider">/</span>
                      <span className="total-count">{category.mistakes}</span>
                    </div>
                  </div>

                  <h3 className="subject-name">{category.subject}</h3>
                  
                  <div className="progress-wrapper">
                    <div className="progress-track">
                      <div 
                        className="progress-bar"
                        style={{ width: `${(category.corrected / category.mistakes) * 100}%` }}
                      />
                    </div>
                    <span className="progress-percent">
                      {Math.round((category.corrected / category.mistakes) * 100)}%
                    </span>
                  </div>

                  <div className="topic-pills">
                    {category.topics.map(topic => (
                      <span key={topic} className="topic-pill">{topic}</span>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* Recent Mistakes Timeline */}
        <section className="recent-section">
          <div className="section-header">
            <h2 className="section-title">Recent Mistakes</h2>
            <button className="view-all-btn">View All <span>→</span></button>
          </div>
          
          <div className="mistakes-timeline">
            {recentMistakes.map((mistake, index) => (
              <motion.div
                key={mistake.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + index * 0.08 }}
                className="timeline-item"
              >
                <div className={`timeline-status ${mistake.status}`}>
                  {mistake.status === 'reviewed' ? (
                    <CheckCircle size={16} />
                  ) : (
                    <AlertCircle size={16} />
                  )}
                </div>

                <div className="timeline-content">
                  <div className="content-header">
                    <span className={`subject-tag ${mistake.subject.toLowerCase()}`}>
                      {mistake.subject}
                    </span>
                    <span className="date">{mistake.date}</span>
                  </div>
                  
                  <p className="question">{mistake.question}</p>
                  
                  <div className="answers-row">
                    <div className="answer wrong">
                      <span className="label">Your answer</span>
                      <code>{mistake.yourAnswer}</code>
                    </div>
                    <div className="answer-divider"></div>
                    <div className="answer correct">
                      <span className="label">Correct</span>
                      <code>{mistake.correctAnswer}</code>
                    </div>
                  </div>
                </div>

                <button className={`review-btn ${mistake.status}`}>
                  <BookOpen size={16} />
                  {mistake.status === 'reviewed' ? 'Reviewed' : 'Review'}
                </button>
              </motion.div>
            ))}
          </div>
        </section>
      </main>
    </motion.div>
  );
}

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, FileText, Clock, Calculator, FlaskConical, BookOpen, ArrowRight, Calendar } from 'lucide-react';
import type { PageType } from '@/types';
import './RevisionPage.css';

interface DailyRecommendationPageProps {
  onPageChange: (_page: PageType) => void;
}

interface Paper {
  id: string;
  subject: string;
  title: string;
  description: string;
  color: string;
  updated: string;
  pages: number;
  author: string;
  publishDate: string;
}

const subjectIcons: Record<string, React.ElementType> = {
  Math: Calculator,
  Science: FlaskConical,
  History: BookOpen,
};

const dailyPapers: Paper[] = [
  {
    id: 'paper-1',
    subject: 'Science',
    title: 'Recent Advances in Quantum Computing',
    description: 'A comprehensive review of quantum computing breakthroughs in 2025, including error correction and practical applications.',
    color: 'emerald',
    updated: 'Today',
    pages: 15,
    author: 'Dr. Sarah Chen',
    publishDate: '2025-02-28'
  },
  {
    id: 'paper-2',
    subject: 'Math',
    title: 'New Methods in Algebraic Topology',
    description: 'Exploring innovative approaches to solving complex topological problems using machine learning algorithms.',
    color: 'blue',
    updated: 'Yesterday',
    pages: 22,
    author: 'Prof. Michael Roberts',
    publishDate: '2025-02-27'
  },
  {
    id: 'paper-3',
    subject: 'History',
    title: 'Digital Archives in Modern Historiography',
    description: 'How AI is revolutionizing historical research through automated document analysis and pattern recognition.',
    color: 'orange',
    updated: '2 days ago',
    pages: 18,
    author: 'Dr. Emily Watson',
    publishDate: '2025-02-26'
  },
  {
    id: 'paper-4',
    subject: 'Science',
    title: 'Climate Change Mitigation Strategies',
    description: 'An in-depth analysis of global warming solutions and renewable energy technologies for a sustainable future.',
    color: 'emerald',
    updated: '3 days ago',
    pages: 25,
    author: 'Prof. James Liu',
    publishDate: '2025-02-25'
  },
  {
    id: 'paper-5',
    subject: 'Math',
    title: 'Statistical Models in Financial Forecasting',
    description: 'Advanced statistical techniques for predicting market trends and economic indicators with higher accuracy.',
    color: 'blue',
    updated: '4 days ago',
    pages: 20,
    author: 'Dr. Anna Martinez',
    publishDate: '2025-02-24'
  },
  {
    id: 'paper-6',
    subject: 'History',
    title: 'Ancient Civilizations and Technology',
    description: 'Uncovering the technological achievements of ancient societies and their influence on modern innovations.',
    color: 'orange',
    updated: '5 days ago',
    pages: 16,
    author: 'Prof. David Brown',
    publishDate: '2025-02-23'
  },
];

export default function DailyRecommendationPage({ onPageChange }: DailyRecommendationPageProps) {
  const [showName, setShowName] = useState(true);
  const [nameOpacity, setNameOpacity] = useState(0);

  // Initial name display animation
  useEffect(() => {
    const fadeInTimer = setTimeout(() => {
      setNameOpacity(1);
    }, 100);

    const fadeOutTimer = setTimeout(() => {
      setNameOpacity(0);
    }, 1200);

    const hideTimer = setTimeout(() => {
      setShowName(false);
    }, 1700);

    return () => {
      clearTimeout(fadeInTimer);
      clearTimeout(fadeOutTimer);
      clearTimeout(hideTimer);
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="revision-page"
    >
      {/* Initial Name Display Overlay */}
      {showName && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="fixed inset-0 bg-white z-50 flex flex-col items-center justify-center"
        >
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: nameOpacity, y: nameOpacity ? 0 : 20 }}
            transition={{ duration: 0.4 }}
            className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 tracking-[0.15em]"
          >
            chur-gpt
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: nameOpacity * 0.8, y: nameOpacity ? 0 : 10 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-gray-500 text-lg mt-4 font-light"
          >
            Daily Recommendations
          </motion.p>
        </motion.div>
      )}

      <main className={`page-content transition-opacity duration-500 ${showName ? 'opacity-0' : 'opacity-100'}`}>
        {/* Hero Section */}
        <section className="hero-section">
          <motion.div 
            className="hero-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="hero-icon">
              <Calendar size={32} />
            </div>
            <div className="hero-text">
              <h2>Daily Paper Recommendations</h2>
              <p>Curated academic papers tailored to your interests and study progress</p>
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <span className="stat-num">{dailyPapers.length}</span>
                <span className="stat-label">Papers</span>
              </div>
              <div className="hero-stat">
                <span className="stat-num">3</span>
                <span className="stat-label">Subjects</span>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Papers Grid */}
        <section className="notes-section">
          <div className="section-header">
            <div>
              <h2 className="section-title">Today's Recommendations</h2>
              <p className="section-subtitle">Fresh academic papers selected for you</p>
            </div>
          </div>

          <div className="notes-grid">
            {dailyPapers.map((paper, index) => {
              const SubjectIcon = subjectIcons[paper.subject] || FileText;
              return (
                <motion.div
                  key={paper.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + index * 0.08 }}
                  className={`note-card ${paper.color} paper-note`}
                >
                  <div className="card-glow" />

                  <div className="card-header">
                    <div className="header-left">
                      <div className="subject-icon-wrapper">
                        <SubjectIcon size={20} />
                      </div>
                      <span className="subject-name">{paper.subject}</span>
                    </div>
                    <div className="ai-indicator">
                      <Sparkles size={12} />
                      <span>Daily Rec</span>
                    </div>
                  </div>

                  <div className="card-body">
                    <h3 className="note-title">{paper.title}</h3>
                    <p className="note-description">{paper.description}</p>
                    <p className="text-sm text-gray-500 mt-2">by {paper.author}</p>
                  </div>

                  <div className="card-footer">
                    <div className="footer-meta">
                      <span className="meta-item">
                        <FileText size={14} />
                        {paper.pages} pages
                      </span>
                      <span className="meta-item">
                        <Clock size={14} />
                        {paper.updated}
                      </span>
                    </div>
                    
                    <button className="open-btn">
                      <span>Read</span>
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </section>
      </main>
    </motion.div>
  );
}

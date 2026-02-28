import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from '@/components/Navbar';
import HeroSection from '@/sections/HeroSection';
import TeacherDashboard from '@/sections/TeacherDashboard';
import TeacherAnalytics from '@/sections/TeacherAnalytics';
import TeacherAssignmentsPage from '@/sections/TeacherAssignmentsPage';
import ClassesPage from '@/sections/ClassesPage';
import AssignmentsPage from '@/sections/AssignmentsPage';
import StartPage from '@/sections/StartPage';
import IntroScreen from '@/sections/IntroScreen';
import RevisionPage from '@/sections/RevisionPage';
import HomeworkPage from '@/sections/HomeworkPage';
import MistakesPage from '@/sections/MistakesPage';
import DailyRecommendationPage from '@/sections/DailyRecommendationPage';
import AIEnhancementEditor from '@/sections/AIEnhancementEditor';
import type { PageType } from '@/types';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('intro');
  const [isNavVisible, setIsNavVisible] = useState(true);

  const handlePageChange = useCallback((page: PageType) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    if (page === 'home') {
      window.history.pushState(null, '', '/');
    } else {
      window.history.pushState(null, '', `#/${page}`);
    }
  }, []);

  useEffect(() => {
    if (currentPage === 'intro' || currentPage === 'home') {
      setIsNavVisible(false);
    } else {
      setIsNavVisible(true);
    }
  }, [currentPage]);

  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const page = hash.replace('#/', '') as PageType;
      if (['teacher-dashboard', 'dashboard', 'revision', 'homework', 'mistakes', 'daily-recommendation', 'teacher-classes', 'teacher-assignments', 'teacher-analytics', 'assignments', 'classes', 'ai-enhancement-editor'].includes(page)) {
        setCurrentPage(page);
      }
    }
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      const hash = window.location.hash;
      if (hash) {
        const page = hash.replace('#/', '') as PageType;
        if (['teacher-dashboard', 'dashboard', 'revision', 'homework', 'mistakes', 'daily-recommendation', 'teacher-classes', 'teacher-assignments', 'teacher-analytics', 'assignments', 'classes', 'ai-enhancement-editor'].includes(page)) {
          setCurrentPage(page);
        } else {
          setCurrentPage('home');
        }
      } else {
        setCurrentPage('home');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleIntroComplete = () => {
    setCurrentPage('home');
  };

  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'intro':
        return (
          <motion.div key="intro">
            <IntroScreen onComplete={handleIntroComplete} />
          </motion.div>
        );
        
      case 'home':
        return (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-50"
          >
            <StartPage onPageChange={handlePageChange} />
          </motion.div>
        );
        
      case 'dashboard':
        return (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <HeroSection onPageChange={handlePageChange} />
          </motion.div>
        );
        
      case 'teacher-dashboard':
        return (
          <motion.div
            key="teacher-dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <TeacherDashboard onPageChange={handlePageChange} />
          </motion.div>
        );

      case 'teacher-analytics':
        return (
          <motion.div
            key="teacher-analytics"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <TeacherAnalytics onPageChange={handlePageChange} />
          </motion.div>
        );

      case 'teacher-assignments':
        return (
          <motion.div
            key="teacher-assignments"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <TeacherAssignmentsPage onPageChange={handlePageChange} />
          </motion.div>
        );

      case 'teacher-classes':
        return (
          <motion.div
            key="teacher-classes"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ClassesPage onPageChange={handlePageChange} />
          </motion.div>
        );

      case 'assignments':
        return (
          <motion.div
            key="assignments"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <AssignmentsPage onPageChange={handlePageChange} />
          </motion.div>
        );

      case 'classes':
        return (
          <motion.div
            key="classes"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ClassesPage onPageChange={handlePageChange} />
          </motion.div>
        );
        
      case 'revision':
        return (
          <motion.div
            key="revision"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <RevisionPage onPageChange={handlePageChange} />
          </motion.div>
        );
        
      case 'homework':
        return (
          <motion.div
            key="homework"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <HomeworkPage onPageChange={handlePageChange} />
          </motion.div>
        );
        
      case 'mistakes':
        return (
          <motion.div
            key="mistakes"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <MistakesPage onPageChange={handlePageChange} />
          </motion.div>
        );
      case 'daily-recommendation':
        return (
          <motion.div
            key="daily-recommendation"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <DailyRecommendationPage onPageChange={handlePageChange} />
          </motion.div>
        );


      case 'ai-enhancement-editor':
        return (
          <motion.div
            key="ai-enhancement-editor"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <AIEnhancementEditor onPageChange={handlePageChange} />
          </motion.div>
        );
        
      default:
        return (
          <motion.div key="intro">
            <IntroScreen onComplete={handleIntroComplete} />
          </motion.div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {currentPage !== 'intro' && currentPage !== 'home' && (
        <Navbar
          currentPage={currentPage}
          onPageChange={handlePageChange}
          isVisible={isNavVisible}
        />
      )}
      
      <main className="relative">
        <AnimatePresence mode="wait">
          {renderPage()}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;

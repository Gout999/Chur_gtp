import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from '@/components/Navbar';
import HeroSection from '@/sections/HeroSection';
import TeacherDashboard from '@/sections/TeacherDashboard';
import StartPage from '@/sections/StartPage';
import RevisionPage from '@/sections/RevisionPage';
import HomeworkPage from '@/sections/HomeworkPage';
import MistakesPage from '@/sections/MistakesPage';
import type { PageType } from '@/types';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('home');
  const [isNavVisible, setIsNavVisible] = useState(true);

  // Handle page change
  const handlePageChange = useCallback((page: PageType) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Update URL hash
    if (page === 'home') {
      window.history.pushState(null, '', '/');
    } else {
      window.history.pushState(null, '', `#/${page}`);
    }
  }, []);

  // Handle navbar visibility
  useEffect(() => {
    if (currentPage === 'home') {
      setIsNavVisible(false);
    } else if (currentPage === 'dashboard' || currentPage === 'teacher-dashboard') {
      setIsNavVisible(true);
    } else {
      setIsNavVisible(true);
    }
  }, [currentPage]);

  // Handle URL hash on load
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const page = hash.replace('#/', '') as PageType;
      if (['teacher-dashboard', 'dashboard', 'revision', 'homework', 'mistakes', 'teacher-classes', 'teacher-assignments', 'teacher-analytics'].includes(page)) {
        setCurrentPage(page);
      }
    }
  }, []);

  // Handle browser back/forward
  useEffect(() => {
    const handlePopState = () => {
      const hash = window.location.hash;
      if (hash) {
        const page = hash.replace('#/', '') as PageType;
        if (['teacher-dashboard', 'dashboard', 'revision', 'homework', 'mistakes'].includes(page)) {
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

  // Page transition variants
  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
      case 'dashboard':
      case 'teacher-dashboard':
        return (
          <motion.div
            key="home-dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            {currentPage === 'teacher-dashboard' ? (
              <TeacherDashboard onPageChange={handlePageChange} />
            ) : (
              <HeroSection onPageChange={handlePageChange} />
            )}
            {currentPage === 'home' && (
              <motion.div
                initial={{ opacity: 1 }}
                exit={{ opacity: 0, transition: { duration: 0.3 } }}
                className="fixed inset-0 z-50"
              >
                <StartPage onPageChange={handlePageChange} />
              </motion.div>
            )}
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
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {currentPage !== 'home' && (
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

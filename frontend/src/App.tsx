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
  const [lastScrollY, setLastScrollY] = useState(0);

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

  // Handle scroll for navbar visibility
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Always show nav on hero, hide on scroll down, show on scroll up
      if (currentPage === 'home') {
        setIsNavVisible(false); // Hide on startpage
      } else if (currentPage === 'dashboard') {
        setIsNavVisible(true);
      } else {
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
          setIsNavVisible(false);
        } else {
          setIsNavVisible(true);
        }
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY, currentPage]);

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
            <AnimatePresence>
              {currentPage === 'home' && (
                <motion.div
                  key="startpage"
                  exit={{ opacity: 0, transition: { duration: 0.8 } }}
                  className="fixed inset-0 z-50"
                >
                  <StartPage onPageChange={handlePageChange} />
                </motion.div>
              )}
            </AnimatePresence>
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

      {/* Footer */}
      {(currentPage !== 'home' && currentPage !== 'dashboard') && (
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gray-900 text-white py-12 px-4"
        >
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="text-center md:text-left">
                <h3 className="text-xl font-medium tracking-wider mb-2">
                  CHARLES ELENA.
                </h3>
                <p className="text-gray-400 text-sm">Do what matters</p>
              </div>
              
              <div className="flex items-center gap-6">
                <button
                  onClick={() => handlePageChange('revision')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Revision
                </button>
                <button
                  onClick={() => handlePageChange('homework')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Homework
                </button>
                <button
                  onClick={() => handlePageChange('mistakes')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Mistakes
                </button>
                </div>
              
              <div className="text-gray-500 text-sm">
                © 2024 Charles Elena. All rights reserved.
              </div>
            </div>
          </div>
        </motion.footer>
      )}
    </div>
  );
}

export default App;

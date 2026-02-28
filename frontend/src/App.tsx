import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from '@/components/Navbar';
import HeroSection from '@/sections/HeroSection';
import CreatePage from '@/sections/CreatePage';
import GrowPage from '@/sections/GrowPage';
import ExperiencePage from '@/sections/ExperiencePage';
import DelightPage from '@/sections/DelightPage';
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
      if (['create', 'grow', 'experience', 'delight'].includes(page)) {
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
        if (['create', 'grow', 'experience', 'delight'].includes(page)) {
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
        return (
          <motion.div
            key="home"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <HeroSection onPageChange={handlePageChange} />
          </motion.div>
        );
      case 'create':
        return (
          <motion.div
            key="create"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <CreatePage onPageChange={handlePageChange} />
          </motion.div>
        );
      case 'grow':
        return (
          <motion.div
            key="grow"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <GrowPage onPageChange={handlePageChange} />
          </motion.div>
        );
      case 'experience':
        return (
          <motion.div
            key="experience"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <ExperiencePage onPageChange={handlePageChange} />
          </motion.div>
        );
      case 'delight':
        return (
          <motion.div
            key="delight"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.5 }}
          >
            <DelightPage onPageChange={handlePageChange} />
          </motion.div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Navbar
        currentPage={currentPage}
        onPageChange={handlePageChange}
        isVisible={isNavVisible}
      />
      
      <main className="relative">
        <AnimatePresence mode="wait">
          {renderPage()}
        </AnimatePresence>
      </main>

      {/* Footer */}
      {currentPage !== 'home' && (
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
                  onClick={() => handlePageChange('create')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Create
                </button>
                <button
                  onClick={() => handlePageChange('grow')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Grow
                </button>
                <button
                  onClick={() => handlePageChange('experience')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Experience
                </button>
                <button
                  onClick={() => handlePageChange('delight')}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Delight
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

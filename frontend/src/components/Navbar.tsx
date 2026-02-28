import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import type { PageType } from '@/types';

interface NavbarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
  isVisible: boolean;
}

export default function Navbar({ currentPage, onPageChange, isVisible }: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Dynamic navigation items based on current page
  const getNavItems = () => {
    const teacherPages = ['teacher-dashboard', 'teacher-classes', 'teacher-assignments', 'teacher-analytics'];
    const isTeacher = teacherPages.includes(currentPage);
    
    if (isTeacher) {
      // Teacher Navigation: Home, Classes, Assignments, Analytics
      return [
        { label: 'Home', page: 'home' as PageType },
        { label: 'Classes', page: 'teacher-classes' as PageType },
        { label: 'Assignments', page: 'teacher-assignments' as PageType },
        { label: 'Analytics', page: 'teacher-analytics' as PageType },
      ];
    } else {
      // Student Navigation: Home, Revision, Assignments, Daily Recommendation
      return [
        { label: 'Home', page: 'home' as PageType },
        { label: 'Revision', page: 'revision' as PageType },
        { label: 'Assignments', page: 'assignments' as PageType },
        { label: 'Daily Recommendation', page: 'daily-recommendation' as PageType },
      ];
      return [
        { label: 'Home', page: 'home' as PageType },
        { label: 'Revision', page: 'revision' as PageType },
        { label: 'Assignments', page: 'assignments' as PageType },
        { label: 'Mistakes', page: 'mistakes' as PageType },
      ];
    }
  };

  const navItems = getNavItems();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (page: PageType) => {
    onPageChange(page);
    setIsMobileMenuOpen(false);
  };

  const isOnDashboard = currentPage === 'dashboard' || currentPage === 'teacher-dashboard';

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: isVisible ? 0 : -100 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled || !isOnDashboard
          ? 'bg-white/95 backdrop-blur-md shadow-sm'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <button
                key={item.label}
                onClick={() => handleNavClick(item.page)}
                className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                  isScrolled || !isOnDashboard
                    ? 'text-gray-800 hover:text-[#E91E8C]'
                    : 'text-white hover:text-[#E91E8C]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Center Logo */}
          <button
            onClick={() => handleNavClick('home')}
            className={`text-lg font-medium tracking-wider transition-colors duration-200 ${
              isScrolled || !isOnDashboard
                ? 'text-gray-900'
                : 'text-white'
            }`}
          >

          </button>

          {/* Right CTA - Disabled */}
          <div className="hidden md:block">
            {/* Button removed as requested */}
          </div>
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className={`md:hidden p-2 rounded-lg transition-colors ${
              isScrolled || !isOnDashboard
                ? 'text-gray-800 hover:bg-gray-100'
                : 'text-white hover:bg-white/10'
            }`}
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-white border-t"
          >
            <div className="px-4 py-4 space-y-2">
              {navItems.map((item) => (
                <button
                  key={item.label}
                  onClick={() => handleNavClick(item.page)}
                  className="block w-full text-left px-4 py-3 text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {item.label}
                </button>
              ))}
              {/* Mobile CTA button removed */}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}

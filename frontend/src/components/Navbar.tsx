import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Menu, X } from 'lucide-react';
import type { PageType } from '@/types';

interface NavbarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
  isVisible: boolean;
}

export default function Navbar({ currentPage, onPageChange, isVisible }: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  // Dynamic navigation items based on current page
  const getNavItems = () => {
    const isTeacher = currentPage === 'teacher-dashboard';
    return [
      { label: isTeacher ? '老師' : 'Home', page: (isTeacher ? 'teacher-dashboard' : 'dashboard') as PageType, hasDropdown: true },
      { label: 'Case Studies', page: 'mistakes' as PageType, hasDropdown: false },
      { label: 'Insights', page: 'mistakes' as PageType, hasDropdown: false },
      { label: 'About', page: 'mistakes' as PageType, hasDropdown: false },
    ];
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
    setActiveDropdown(null);
  };

  const getHomePage = () => currentPage === 'teacher-dashboard' ? 'teacher-dashboard' : 'dashboard';

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
              <div
                key={item.label}
                className="relative"
                onMouseEnter={() => item.hasDropdown && setActiveDropdown(item.label)}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button
                  onClick={() => handleNavClick(item.page)}
                  className={`flex items-center px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                    isScrolled || !isOnDashboard
                      ? 'text-gray-800 hover:text-[#E91E8C]'
                      : 'text-white hover:text-[#E91E8C]'
                  }`}
                >
                  {item.label}
                  {item.hasDropdown && (
                    <ChevronDown className="ml-1 w-4 h-4" />
                  )}
                </button>

                {/* Dropdown */}
                <AnimatePresence>
                  {item.hasDropdown && activeDropdown === item.label && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{ duration: 0.2 }}
                      className="absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-lg py-2"
                    >
                      <button
                        onClick={() => handleNavClick(getHomePage())}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-[#E91E8C]"
                      >
                        {currentPage === 'teacher-dashboard' ? '老師' : 'Home'}
                      </button>
                      <button
                        onClick={() => handleNavClick(currentPage === 'teacher-dashboard' ? 'dashboard' : 'teacher-dashboard')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-[#E91E8C]"
                      >
                        {currentPage === 'teacher-dashboard' ? '學生' : '老師'}
                      </button>
                      <button
                        onClick={() => handleNavClick('revision')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-[#E91E8C]"
                      >
                        Revision
                      </button>
                      <button
                        onClick={() => handleNavClick('homework')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-[#E91E8C]"
                      >
                        Homework
                      </button>
                      <button
                        onClick={() => handleNavClick('mistakes')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-[#E91E8C]"
                      >
                        Mistakes
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>

          {/* Center Logo */}
          <button
            onClick={() => handleNavClick(getHomePage())}
            className={`text-lg font-medium tracking-wider transition-colors duration-200 ${
              isScrolled || !isOnDashboard
                ? 'text-gray-900'
                : 'text-white'
            }`}
          >
            chur-gpt.
          </button>

          {/* Right CTA */}
          <div className="hidden md:block">
            <button
              onClick={() => handleNavClick('mistakes')}
              className="btn-dark text-sm"
            >
              Contact us Today
            </button>
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
              <button
                onClick={() => handleNavClick('mistakes')}
                className="btn-dark w-full text-center mt-4"
              >
                Contact us Today
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}

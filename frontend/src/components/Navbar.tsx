import { motion } from 'framer-motion';
import type { PageType } from '@/types';

interface NavbarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
  isVisible: boolean;
}

export default function Navbar({ currentPage, onPageChange, isVisible }: NavbarProps) {
  const teacherPages: PageType[] = ['teacher-dashboard', 'teacher-classes', 'teacher-assignments', 'teacher-analytics'];
  const isTeacher = teacherPages.includes(currentPage);

  const navItems = isTeacher
    ? [
        { label: 'Classes', page: 'teacher-classes' as PageType },
        { label: 'Assignments', page: 'teacher-assignments' as PageType },
        { label: 'Analytics', page: 'teacher-analytics' as PageType },
      ]
    : [
        { label: 'Revision', page: 'revision' as PageType },
        { label: 'Assignments', page: 'assignments' as PageType },
        { label: 'Daily Recommendation', page: 'daily-recommendation' as PageType },
      ];

  const isActive = (page: PageType) => page === currentPage;

  return (
    <motion.nav
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: isVisible ? 0 : -60, opacity: isVisible ? 1 : 0 }}
      transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      className="fixed top-3 left-4 right-4 z-[60] flex justify-center pointer-events-none"
    >
      <div
        className="pointer-events-auto w-full max-w-3xl flex items-center justify-between px-6 py-3 rounded-2xl border border-black/10"
        style={{
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'saturate(180%) blur(20px)',
          WebkitBackdropFilter: 'saturate(180%) blur(20px)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.06)',
        }}
      >
        {/* Logo → Home */}
        <button
          onClick={() => onPageChange('home')}
          className="text-[15px] font-semibold tracking-tight text-black/90 hover:text-[#E91E8C] transition-colors shrink-0"
        >
          chur-gpt
        </button>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {navItems.map((item) => (
            <button
              key={item.label}
              onClick={() => onPageChange(item.page)}
              className={`relative px-4 py-1.5 rounded-full text-[13px] font-medium whitespace-nowrap transition-all duration-200 ${
                isActive(item.page)
                  ? 'bg-black text-white shadow-sm'
                  : 'text-black/50 hover:text-black/90 hover:bg-black/[0.04]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </motion.nav>
  );
}

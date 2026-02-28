import { useState } from 'react';
import { motion } from 'framer-motion';
import type { PageType } from '@/types';

interface TeacherDashboardProps {
  onPageChange: (page: PageType) => void;
}

interface ColumnData {
  id: PageType;
  label: string;
  image: string;
  color: string;
}

const columns: ColumnData[] = [
  { id: 'teacher-classes' as PageType, label: 'Classes', image: '/images/revision-bg.jpg', color: 'from-orange-500/20' },
  { id: 'teacher-assignments' as PageType, label: 'Assignments', image: '/images/homework-bg.jpg', color: 'from-cyan-500/20' },
  { id: 'teacher-analytics' as PageType, label: 'Analytics', image: '/images/mistakes-bg.jpg', color: 'from-yellow-500/20' },
];

export default function TeacherDashboard({ onPageChange }: TeacherDashboardProps) {
  const [hoveredColumn, setHoveredColumn] = useState<PageType | null>(null);

  const getColumnWidth = (columnId: PageType) => {
    if (!hoveredColumn) return '33.333%';
    if (hoveredColumn === columnId) return '50%';
    return '25%';
  };

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Four Columns */}
      <div className="flex w-full h-full">
        {columns.map((column, index) => (
          <motion.div
            key={column.id}
            
            animate={{ 
              opacity: 1, 
              y: 0,
              width: getColumnWidth(column.id),
            }}
            transition={{ 
              opacity: { duration: 0.6, delay: index * 0.1 },
              y: { duration: 0.6, delay: index * 0.1 },
              width: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
            }}
            onMouseEnter={() => setHoveredColumn(column.id)}
            onMouseLeave={() => setHoveredColumn(null)}
            onClick={() => onPageChange(column.id)}
            className="relative h-full cursor-pointer overflow-hidden"
            style={{ width: getColumnWidth(column.id) }}
          >
            {/* Background Image */}
            <motion.div
              animate={{ 
                scale: hoveredColumn === column.id ? 1.05 : 1 
              }}
              transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
              className="absolute inset-0"
            >
              <img
                src={column.image}
                alt={column.label}
                className="w-full h-full object-cover"
              />
            </motion.div>

            {/* Overlay */}
            <div className={`absolute inset-0 bg-gradient-to-t ${column.color} to-black/40 transition-opacity duration-300 ${
              hoveredColumn === column.id ? 'opacity-60' : 'opacity-40'
            }`} />

            {/* Column Label */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 + index * 0.1, duration: 0.4 }}
              className="absolute bottom-8 left-1/2 -translate-x-1/2"
            >
              <span className="text-white text-lg font-light tracking-wide">
                {column.label}
              </span>
            </motion.div>

            {/* Hover Indicator */}
            {hoveredColumn === column.id && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-[#E91E8C] rounded-full"
              />
            )}
          </motion.div>
        ))}
      </div>

      {/* Center Branding */}
      <div className="absolute top-8 left-0 right-0 flex flex-col items-center justify-start pointer-events-none z-10">
        <h1 className="text-white text-3xl md:text-4xl lg:text-5xl font-medium tracking-[0.2em]">
          chur-gpt
        </h1>
        <p className="text-white/80 text-lg md:text-xl font-light tracking-wide">
          Select a category below
        </p>
      </div>
    </div>
  );
}

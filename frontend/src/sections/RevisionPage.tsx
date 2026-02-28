import { motion } from 'framer-motion';
import { ArrowRight, Lightbulb } from 'lucide-react';
import type { PageType } from '@/types';

interface CreatePageProps {
  onPageChange: (page: PageType) => void;
}

export default function RevisionPage({ }: CreatePageProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-[#FDFDFD]"
    >
      {/* Hero Section */}
      <div className="relative h-[40vh] overflow-hidden flex items-end pb-12">
        <div className="absolute inset-0">
          <img
            src="/images/revision-bg.jpg"
            alt="Revision"
            className="w-full h-full object-cover blur-sm scale-105"
          />
          <div className="absolute inset-0 bg-white/70 backdrop-blur-md" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#FDFDFD]" />
        </div>

        <div className="relative z-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <h1 className="text-gray-900 text-5xl md:text-6xl font-semibold mb-4 tracking-tight">
              AI Smart Notes
            </h1>
            <p className="text-gray-500 text-lg md:text-xl font-medium max-w-2xl">
              Your personalized, AI-generated revision materials organized for peak performance.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Bento Box Grid Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Note Card 1 */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.5 }}
            className="group relative bg-white rounded-3xl p-8 border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1 hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] transition-all duration-300 cursor-pointer overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-indigo-500 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
            <div className="flex justify-between items-start mb-12">
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-semibold rounded-full">Math</span>
                <span className="px-3 py-1 bg-purple-50 text-purple-600 text-xs font-semibold rounded-full flex items-center gap-1">
                  <Lightbulb className="w-3 h-3" /> AI Generated
                </span>
              </div>
            </div>
            <div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">Factoring Polynomials</h3>
              <p className="text-gray-500 line-clamp-2">Master the techniques of factoring complex polynomial equations with step-by-step AI breakdowns and visual aids.</p>
            </div>
            <div className="mt-8 flex items-center text-sm font-medium text-gray-400">
              <span>Updated 2h ago</span>
              <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 text-blue-600" />
            </div>
          </motion.div>

          {/* Note Card 2 */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="group relative bg-white rounded-3xl p-8 border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1 hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] transition-all duration-300 cursor-pointer overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-teal-500 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
            <div className="flex justify-between items-start mb-12">
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-semibold rounded-full">Science</span>
                <span className="px-3 py-1 bg-purple-50 text-purple-600 text-xs font-semibold rounded-full flex items-center gap-1">
                  <Lightbulb className="w-3 h-3" /> AI Generated
                </span>
              </div>
            </div>
            <div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3 group-hover:text-emerald-600 transition-colors">Cellular Respiration</h3>
              <p className="text-gray-500 line-clamp-2">A comprehensive guide to glycolysis, the Krebs cycle, and electron transport chains simplified by AI.</p>
            </div>
            <div className="mt-8 flex items-center text-sm font-medium text-gray-400">
              <span>Updated 5h ago</span>
              <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 text-emerald-600" />
            </div>
          </motion.div>

          {/* Note Card 3 */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="group relative bg-white rounded-3xl p-8 border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1 hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] transition-all duration-300 cursor-pointer overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-400 to-red-500 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
            <div className="flex justify-between items-start mb-12">
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-orange-50 text-orange-600 text-xs font-semibold rounded-full">History</span>
                <span className="px-3 py-1 bg-purple-50 text-purple-600 text-xs font-semibold rounded-full flex items-center gap-1">
                  <Lightbulb className="w-3 h-3" /> AI Generated
                </span>
              </div>
            </div>
            <div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3 group-hover:text-orange-600 transition-colors">The Industrial Revolution</h3>
              <p className="text-gray-500 line-clamp-2">Key inventions, societal shifts, and economic impacts summarized with AI-generated timelines.</p>
            </div>
            <div className="mt-8 flex items-center text-sm font-medium text-gray-400">
              <span>Updated 1d ago</span>
              <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 text-orange-600" />
            </div>
          </motion.div>

        </div>
      </section>
    </motion.div>
  );
}

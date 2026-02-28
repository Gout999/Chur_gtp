import { motion } from 'framer-motion';
import { ArrowRight, TrendingUp, Zap, Globe } from 'lucide-react';
import type { PageType } from '@/types';

interface GrowPageProps {
  onPageChange: (page: PageType) => void;
}

const growthAreas = [
  {
    icon: TrendingUp,
    title: 'Business Growth',
    description: 'Data-driven strategies to accelerate your business performance and market presence.',
  },
  {
    icon: Zap,
    title: 'Digital Transformation',
    description: 'Leverage cutting-edge technology to streamline operations and boost efficiency.',
  },
  {
    icon: Globe,
    title: 'Global Expansion',
    description: 'Scale your brand internationally with localized strategies and market insights.',
  },
];

const stats = [
  { value: '150%', label: 'Average Growth' },
  { value: '50+', label: 'Markets Reached' },
  { value: '200M+', label: 'Users Engaged' },
];

export default function GrowPage({ onPageChange }: GrowPageProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-white"
    >
      {/* Hero Section */}
      <div className="relative h-[70vh] overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="/images/grow-bg.jpg"
            alt="Grow"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/60 to-black/30" />
        </div>

        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="text-white text-6xl md:text-7xl lg:text-8xl font-light mb-4"
          >
            Grow
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="text-white/80 text-xl md:text-2xl font-light max-w-xl"
          >
            Scale your business with confidence
          </motion.p>
        </div>
      </div>

      {/* Stats Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-cyan-900">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="text-center"
              >
                <div className="text-4xl md:text-5xl font-light text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-cyan-200">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Growth Areas Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-light text-gray-900 mb-4">
            How We Help You Grow
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Comprehensive solutions designed to accelerate your business growth.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {growthAreas.map((area, index) => (
            <motion.div
              key={area.title}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="bg-gray-50 rounded-2xl p-8 card-lift"
            >
              <div className="w-14 h-14 bg-cyan-100 rounded-xl flex items-center justify-center mb-6">
                <area.icon className="w-7 h-7 text-cyan-600" />
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-3">{area.title}</h3>
              <p className="text-gray-600 leading-relaxed">{area.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-cyan-50">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-light text-gray-900 mb-6">
              Ready to accelerate your growth?
            </h2>
            <p className="text-gray-600 text-lg mb-8">
              Let&apos;s discuss how we can help you reach new heights.
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onPageChange('mistakes')}
              className="btn-dark inline-flex items-center gap-2"
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
}

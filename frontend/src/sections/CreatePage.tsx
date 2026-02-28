import { motion } from 'framer-motion';
import { ArrowRight, Palette, Lightbulb, Layers } from 'lucide-react';
import type { PageType } from '@/types';

interface CreatePageProps {
  onPageChange: (page: PageType) => void;
}

const services = [
  {
    icon: Palette,
    title: 'Brand Design',
    description: 'Crafting visual identities that resonate with your audience and stand the test of time.',
  },
  {
    icon: Lightbulb,
    title: 'Creative Strategy',
    description: 'Innovative approaches to storytelling that capture attention and drive engagement.',
  },
  {
    icon: Layers,
    title: 'Digital Experiences',
    description: 'Building immersive digital products that users love to interact with.',
  },
];

export default function CreatePage({ onPageChange }: CreatePageProps) {
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
            src="/images/create-bg.jpg"
            alt="Create"
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
            Create
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="text-white/80 text-xl md:text-2xl font-light max-w-xl"
          >
            Transform ideas into extraordinary experiences
          </motion.p>
        </div>
      </div>

      {/* Services Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-light text-gray-900 mb-4">
            Our Creative Services
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            We bring your vision to life through strategic design and innovative thinking.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <motion.div
              key={service.title}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="bg-gray-50 rounded-2xl p-8 card-lift"
            >
              <div className="w-14 h-14 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
                <service.icon className="w-7 h-7 text-orange-600" />
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-3">{service.title}</h3>
              <p className="text-gray-600 leading-relaxed">{service.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-orange-50">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-light text-gray-900 mb-6">
              Ready to create something amazing?
            </h2>
            <p className="text-gray-600 text-lg mb-8">
              Let&apos;s collaborate and bring your ideas to life.
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onPageChange('experience')}
              className="btn-dark inline-flex items-center gap-2"
            >
              Start a Project
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
}

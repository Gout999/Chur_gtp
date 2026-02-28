import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { ChevronRight, ChevronDown } from 'lucide-react';
import type { PageType } from '@/types';

interface ExperiencePageProps {
  onPageChange: (page: PageType) => void;
}

const features = [
  {
    title: 'Capture innovation',
    description: 'Leverage technology as your competitive advantage. Let it drive for impact or improvement.',
    icon: 'radial',
    colors: ['#FF6B9D', '#4ECDC4', '#FFE66D'],
  },
  {
    title: 'Create immersion',
    description: 'Digital structures that connect. Creative content and immersive experiences, that inspires you.',
    icon: 'torus',
    colors: ['#667EEA', '#764BA2', '#F093FB'],
  },
  {
    title: 'Gain agility',
    description: 'Adapt to the pace of ambition. We integrate AI into your business to scale, lead and seize opportunity.',
    icon: 'cube',
    colors: ['#4FACFE', '#00F2FE', '#43E97B'],
  },
  {
    title: 'Define experiences',
    description: 'Deeply engage your customers. We create distinctive designs that delight your audiences.',
    icon: 'spiral',
    colors: ['#FA709A', '#FEE140', '#FF6B6B'],
  },
];

const caseStudies = [
  { id: 1, image: '/images/case-1.jpg', title: 'VR Experience', category: 'Immersive' },
  { id: 2, image: '/images/case-2.jpg', title: 'Brand Activation', category: 'Events' },
  { id: 3, image: '/images/case-3.jpg', title: 'Future Mobility', category: 'Automotive' },
  { id: 4, image: '/images/case-4.jpg', title: 'Digital Art', category: 'Creative' },
];

// Abstract Icon Components
function RadialIcon({ colors }: { colors: string[] }) {
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      {[...Array(12)].map((_, i) => (
        <line
          key={i}
          x1="50"
          y1="50"
          x2={50 + 40 * Math.cos((i * 30 * Math.PI) / 180)}
          y2={50 + 40 * Math.sin((i * 30 * Math.PI) / 180)}
          stroke={colors[i % colors.length]}
          strokeWidth="3"
          strokeLinecap="round"
        />
      ))}
      <circle cx="50" cy="50" r="15" fill={colors[0]} opacity="0.3" />
    </svg>
  );
}

function TorusIcon({ colors }: { colors: string[] }) {
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <defs>
        <linearGradient id="torusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors[0]} />
          <stop offset="50%" stopColor={colors[1]} />
          <stop offset="100%" stopColor={colors[2]} />
        </linearGradient>
      </defs>
      <ellipse
        cx="50"
        cy="50"
        rx="35"
        ry="25"
        fill="none"
        stroke="url(#torusGrad)"
        strokeWidth="8"
        transform="rotate(45 50 50)"
      />
      <ellipse
        cx="50"
        cy="50"
        rx="20"
        ry="15"
        fill="none"
        stroke="url(#torusGrad)"
        strokeWidth="4"
        opacity="0.5"
        transform="rotate(45 50 50)"
      />
    </svg>
  );
}

function CubeIcon({ colors }: { colors: string[] }) {
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <defs>
        <linearGradient id="cubeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors[0]} />
          <stop offset="100%" stopColor={colors[1]} />
        </linearGradient>
      </defs>
      <path
        d="M50 20 L80 35 L80 65 L50 80 L20 65 L20 35 Z"
        fill="none"
        stroke="url(#cubeGrad)"
        strokeWidth="2"
      />
      <path
        d="M50 20 L50 50 L80 35"
        fill="none"
        stroke={colors[0]}
        strokeWidth="2"
      />
      <path
        d="M50 50 L50 80 L20 65"
        fill="none"
        stroke={colors[1]}
        strokeWidth="2"
      />
      <path
        d="M50 50 L80 35 L80 65"
        fill="none"
        stroke={colors[2]}
        strokeWidth="2"
      />
    </svg>
  );
}

function SpiralIcon({ colors }: { colors: string[] }) {
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <defs>
        <linearGradient id="spiralGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors[0]} />
          <stop offset="50%" stopColor={colors[1]} />
          <stop offset="100%" stopColor={colors[2]} />
        </linearGradient>
      </defs>
      <path
        d="M50 50 Q70 30 50 20 Q30 10 20 30 Q10 50 30 70 Q50 90 70 70 Q90 50 70 30"
        fill="none"
        stroke="url(#spiralGrad)"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}

function FeatureIcon({ icon, colors }: { icon: string; colors: string[] }) {
  switch (icon) {
    case 'radial':
      return <RadialIcon colors={colors} />;
    case 'torus':
      return <TorusIcon colors={colors} />;
    case 'cube':
      return <CubeIcon colors={colors} />;
    case 'spiral':
      return <SpiralIcon colors={colors} />;
    default:
      return null;
  }
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="bg-gray-50 rounded-2xl p-6 card-lift"
    >
      <div className="w-20 h-20 mb-4">
        <FeatureIcon icon={feature.icon} colors={feature.colors} />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{feature.title}</h3>
      <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
    </motion.div>
  );
}

function CaseStudyCard({ study, index }: { study: typeof caseStudies[0]; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="relative overflow-hidden rounded-xl group cursor-pointer"
    >
      <div className="aspect-[4/3] overflow-hidden">
        <img
          src={study.image}
          alt={study.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute bottom-4 left-4 text-white">
          <span className="text-xs uppercase tracking-wider opacity-70">{study.category}</span>
          <h4 className="text-lg font-medium">{study.title}</h4>
        </div>
      </div>
    </motion.div>
  );
}

export default function ExperiencePage({ onPageChange }: ExperiencePageProps) {
  const heroRef = useRef(null);
  const heroInView = useInView(heroRef, { once: true });
  
  // Use onPageChange to avoid TypeScript error
  const handleContactClick = () => {
    onPageChange('mistakes');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-white"
    >
      {/* Hero Section */}
      <div ref={heroRef} className="relative h-screen overflow-hidden">
        {/* Background Video/Image */}
        <div className="absolute inset-0">
          <img
            src="/images/mistakes-bg.jpg"
            alt="Experience"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={heroInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="text-white text-6xl md:text-7xl lg:text-8xl font-light mb-4"
          >
            Experience
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={heroInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="text-white/80 text-xl md:text-2xl font-light"
          >
            digital transformation
          </motion.p>
        </div>

        {/* Scroll Down Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={heroInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/70 flex flex-col items-center gap-2"
        >
          <span className="text-sm">Scroll down</span>
          <ChevronDown className="w-5 h-5 animate-bounce" />
        </motion.div>
      </div>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-light text-gray-900 mb-4">
            Where leaders make ambition reality
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={feature} index={index} />
          ))}
        </div>
      </section>

      {/* Moments Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-pink-50">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-light text-gray-900 mb-6">
              Moments that<br />capture you
            </h2>
            <p className="text-gray-600 text-lg leading-relaxed max-w-2xl mx-auto">
              By solving complexity with elegance, we create digital moments that elevate brands 
              and reassure their audiences. We design immersive applications with AI-enabled 
              platforms to web, VR, and spatial technologies.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Case Studies Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-12">
          <motion.h2
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl md:text-4xl font-light text-gray-900"
          >
            Case Studies
          </motion.h2>
          <motion.button
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            whileHover={{ x: 5 }}
            onClick={handleContactClick}
            className="flex items-center gap-2 text-gray-600 hover:text-[#E91E8C] transition-colors"
          >
            View all
            <ChevronRight className="w-4 h-4" />
          </motion.button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {caseStudies.map((study, index) => (
            <CaseStudyCard key={study.id} study={study} index={index} />
          ))}
        </div>
      </section>
    </motion.div>
  );
}

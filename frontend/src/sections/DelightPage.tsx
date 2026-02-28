import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ChevronRight } from 'lucide-react';
import type { PageType } from '@/types';

interface DelightPageProps {
  onPageChange: (page: PageType) => void;
}

const carouselImages = [
  { id: 1, src: '/images/delight-1.jpg', alt: 'Sydney Opera House' },
  { id: 2, src: '/images/delight-2.jpg', alt: 'Uluru' },
  { id: 3, src: '/images/delight-3.jpg', alt: 'Great Barrier Reef' },
  { id: 4, src: '/images/delight-4.jpg', alt: 'Rainforest Waterfall' },
];

const sidebarItems: PageType[] = ['create', 'grow', 'experience'];

export default function DelightPage({ onPageChange }: DelightPageProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % carouselImages.length);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="relative min-h-screen"
    >
      {/* Background Carousel */}
      <div className="absolute inset-0 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentImageIndex}
            initial={{ opacity: 0, scale: 1.1 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            transition={{ duration: 0.8 }}
            className="absolute inset-0"
          >
            <img
              src={carouselImages[currentImageIndex].src}
              alt={carouselImages[currentImageIndex].alt}
              className="w-full h-full object-cover"
            />
          </motion.div>
        </AnimatePresence>
        
        {/* Dark Overlay */}
        <div className="absolute inset-0 bg-black/30" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-center"
        >
          <h1 className="text-white text-6xl md:text-7xl lg:text-8xl font-light mb-6">
            Delight
          </h1>
          <p className="text-white/90 text-lg md:text-xl max-w-xl mx-auto mb-8 leading-relaxed">
            Unleash your imagination and create your own selfie post-card in seconds!
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-primary flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Generate
            </motion.button>
          </div>
          
          <motion.button
            whileHover={{ x: 5 }}
            className="mt-4 text-white/80 hover:text-[#E91E8C] flex items-center gap-1 mx-auto transition-colors"
          >
            Surprise me
            <ChevronRight className="w-4 h-4" />
          </motion.button>
        </motion.div>

        {/* Carousel Indicators */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-2">
          {carouselImages.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentImageIndex(index)}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                index === currentImageIndex
                  ? 'bg-white w-6'
                  : 'bg-white/50 hover:bg-white/70'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Right Sidebar Navigation */}
      <div className="absolute right-4 top-1/2 -translate-y-1/2 z-20 hidden lg:flex flex-col gap-3">
        {sidebarItems.map((item, index) => (
          <motion.button
            key={item}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 + index * 0.1 }}
            onClick={() => onPageChange(item)}
            className="group relative w-16 h-16 rounded-lg overflow-hidden border-2 border-white/30 hover:border-white/60 transition-all"
          >
            <img
              src={`/images/${item}-bg.jpg`}
              alt={item}
              className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity"
            />
            <span className="absolute inset-0 flex items-center justify-center text-white text-xs font-medium capitalize">
              {item}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface IntroScreenProps {
  onComplete: () => void;
}

export default function IntroScreen({ onComplete }: IntroScreenProps) {
  const [showText, setShowText] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    // Show text after white screen
    const textTimer = setTimeout(() => {
      setShowText(true);
    }, 300);

    // Start fading out after showing text
    const fadeTimer = setTimeout(() => {
      setFadeOut(true);
    }, 2000);

    // Complete intro after fade out
    const completeTimer = setTimeout(() => {
      onComplete();
    }, 2800);

    return () => {
      clearTimeout(textTimer);
      clearTimeout(fadeTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      animate={{ opacity: fadeOut ? 0 : 1 }}
      transition={{ duration: 0.8, ease: 'easeInOut' }}
      className="fixed inset-0 z-[100] bg-white flex items-center justify-center"
    >
      <AnimatePresence>
        {showText && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          >
            <h1 className="text-6xl md:text-8xl lg:text-9xl font-normal tracking-[0.2em] text-gray-900">
              CHUR-GPT
            </h1>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

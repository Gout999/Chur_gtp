import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, BookOpen, Video, FileText, ExternalLink, MessageCircle, X, Send, Sparkles, Bot, User } from 'lucide-react';
import type { PageType } from '@/types';
import './HomeworkPage.css';

interface HomeworkPageProps {
  onPageChange: (page: PageType) => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

const resources = [
  {
    title: 'Mathematics Fundamentals',
    type: 'Video',
    duration: '45 min',
    subject: 'Math',
    icon: Video,
    color: 'blue'
  },
  {
    title: 'Science Lab Safety Guide',
    type: 'Document',
    pages: 12,
    subject: 'Science',
    icon: FileText,
    color: 'emerald'
  },
  {
    title: 'Essay Writing Tips',
    type: 'Article',
    readTime: '10 min',
    subject: 'English',
    icon: BookOpen,
    color: 'orange'
  },
];

const quickLinks = [
  { label: 'My Assignments', page: 'assignments' as PageType },
  { label: 'Revision Notes', page: 'revision' as PageType },
  { label: 'Mistakes Tracker', page: 'mistakes' as PageType },
];

// Mock AI responses for homework help
const aiResponses: Record<string, string> = {
  default: "I'd be happy to help you with your homework! Could you please tell me which subject and topic you need help with?",
  math: "For math problems, I recommend breaking them down into smaller steps. Would you like me to walk through a specific problem with you?",
  science: "Science concepts can be tricky! Let me explain it in a simpler way. What specific topic are you studying?",
  english: "For English assignments, I can help with essay structure, grammar, or analyzing texts. What do you need help with?",
  help: "I can help you with:\n• Explaining difficult concepts\n• Checking your answers\n• Providing study tips\n• Suggesting resources\n\nWhat would you like assistance with?",
};

export default function HomeworkPage({ onPageChange }: HomeworkPageProps) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      type: 'ai',
      content: "Hi! I'm your AI Homework Assistant. I'm here to help you with any questions about your assignments. What can I help you with today?",
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getAIResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();
    if (lowerMessage.includes('math') || lowerMessage.includes('calculus') || lowerMessage.includes('algebra')) {
      return aiResponses.math;
    } else if (lowerMessage.includes('science') || lowerMessage.includes('physics') || lowerMessage.includes('chemistry')) {
      return aiResponses.science;
    } else if (lowerMessage.includes('english') || lowerMessage.includes('essay') || lowerMessage.includes('grammar')) {
      return aiResponses.english;
    } else if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
      return aiResponses.help;
    }
    return aiResponses.default;
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: getAIResponse(userMsg.content),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="homework-page"
    >
      {/* Hero Section */}
      <div className="homework-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="hero-content"
        >
          <h1>Study Resources</h1>
          <p>Access learning materials and study aids</p>
        </motion.div>
      </div>

      {/* Quick Links */}
      <section className="quick-links-section">
        <h2>Quick Access</h2>
        <div className="quick-links-grid">
          {quickLinks.map((link, index) => (
            <motion.button
              key={link.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index, duration: 0.4 }}
              className="quick-link-card"
              onClick={() => onPageChange(link.page)}
            >
              <span>{link.label}</span>
              <ArrowRight size={18} />
            </motion.button>
          ))}
        </div>
      </section>

      {/* Resources */}
      <section className="resources-section">
        <h2>Recommended Resources</h2>
        
        <div className="resources-grid">
          {resources.map((resource, index) => {
            const Icon = resource.icon;
            return (
              <motion.div
                key={resource.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index, duration: 0.4 }}
                className={`resource-card ${resource.color}`}
              >
                <div className="resource-icon">
                  <Icon size={24} />
                </div>
                
                <div className="resource-content">
                  <span className="subject-tag">{resource.subject}</span>
                  <h3>{resource.title}</h3>
                  <p>
                    {resource.type} • {resource.duration || resource.pages + ' pages' || resource.readTime}
                  </p>
                </div>
                
                <button className="access-btn">
                  <ExternalLink size={16} />
                </button>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* AI Chat Panel - Slides in from left */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ x: -400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -400, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-4 bottom-24 w-[380px] h-[500px] bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden z-50 flex flex-col"
          >
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-500 px-5 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
                  <Sparkles className="text-white" size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-white">AI Homework Assistant</h3>
                  <p className="text-purple-100 text-xs">Always here to help</p>
                </div>
              </div>
              
              <button 
                onClick={() => setIsChatOpen(false)}
                className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
              >
                <X size={18} className="text-white" />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start gap-2 max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      message.type === 'user' 
                        ? 'bg-purple-600' 
                        : 'bg-gradient-to-br from-purple-500 to-pink-500'
                    }`}>
                      {message.type === 'user' ? (
                        <User size={14} className="text-white" />
                      ) : (
                        <Bot size={14} className="text-white" />
                      )}
                    </div>
                    
                    <div className={`px-4 py-2.5 rounded-2xl text-sm whitespace-pre-line ${
                      message.type === 'user'
                        ? 'bg-purple-600 text-white rounded-br-md'
                        : 'bg-gray-100 text-gray-700 rounded-bl-md'
                    }`}>
                      {message.content}
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center gap-2 bg-gray-100 px-4 py-2.5 rounded-2xl rounded-bl-md">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-xs text-gray-500 ml-1">AI is thinking...</span>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your homework..."
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none text-sm bg-white"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  className="w-11 h-11 rounded-xl bg-purple-600 text-white flex items-center justify-center hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send size={18} />
                </button>
              </div>
              
              <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
                {['Explain math', 'Check grammar', 'Study tips', 'Resources'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInputMessage(suggestion)}
                    className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs text-gray-600 hover:border-purple-300 hover:text-purple-600 transition-colors whitespace-nowrap"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating AI Button - Bottom Right */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 1, type: 'spring', stiffness: 200 }}
        onClick={() => setIsChatOpen(!isChatOpen)}
        className={`fixed right-6 bottom-6 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center z-50 transition-all duration-300 ${
          isChatOpen 
            ? 'bg-gray-900 rotate-90' 
            : 'bg-gradient-to-r from-purple-600 to-pink-500 hover:shadow-purple-500/50 hover:scale-110'
        }`}
      >
        {isChatOpen ? (
          <X size={24} className="text-white" />
        ) : (
          <MessageCircle size={28} className="text-white" />
        )}
        
        {/* Pulse animation when closed */}
        {!isChatOpen && (
          <span className="absolute inset-0 rounded-full bg-purple-600 animate-ping opacity-20" />
        )}
      </motion.button>
    </motion.div>
  );
}

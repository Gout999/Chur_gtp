import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Lightbulb, Sparkles, FileText, Clock, Calculator, FlaskConical, BookOpen, Upload, X, CheckCircle, Trash2, AlertCircle, Target } from 'lucide-react';
import type { PageType } from '@/types';
import './RevisionPage.css';


interface RevisionPageProps {
  onPageChange: (_page: PageType) => void;
}

interface Note {
  id: string;
  subject: string;
  title: string;
  description: string;
  color: string;
  updated: string;
  pages: number;
  isCustom?: boolean;
  fileName?: string;
}

const subjectIcons: Record<string, React.ElementType> = {
  Math: Calculator,
  Science: FlaskConical,
  History: BookOpen,
};

const defaultNotes: Note[] = [
  {
    id: '1',
    subject: 'Math',
    title: 'Factoring Polynomials',
    description: 'Master the techniques of factoring complex polynomial equations with step-by-step AI breakdowns and visual aids.',
    color: 'blue',
    updated: '2h ago',
    pages: 12
  },
  {
    id: '2',
    subject: 'Science',
    title: 'Cellular Respiration',
    description: 'A comprehensive guide to glycolysis, the Krebs cycle, and electron transport chains simplified by AI.',
    color: 'emerald',
    updated: '5h ago',
    pages: 18
  },
  {
    id: '3',
    subject: 'History',
    title: 'The Industrial Revolution',
    description: 'Key inventions, societal shifts, and economic impacts summarized with AI-generated timelines.',
    color: 'orange',
    updated: '1d ago',
    pages: 24
  },
];

// Mock daily papers data (for backend integration)
const dailyPapers: Note[] = [
  {
    id: 'paper-1',
    subject: 'Science',
    title: 'Recent Advances in Quantum Computing',
    description: 'A comprehensive review of quantum computing breakthroughs in 2025, including error correction and practical applications.',
    color: 'emerald',
    updated: 'Today',
    pages: 15,
  },
  {
    id: 'paper-2',
    subject: 'Math',
    title: 'New Methods in Algebraic Topology',
    description: 'Exploring innovative approaches to solving complex topological problems using machine learning algorithms.',
    color: 'blue',
    updated: 'Yesterday',
    pages: 22,
  },
  {
    id: 'paper-3',
    subject: 'History',
    title: 'Digital Archives in Modern Historiography',
    description: 'How AI is revolutionizing historical research through automated document analysis and pattern recognition.',
    color: 'orange',
    updated: '2 days ago',
    pages: 18,
  },
];

const recentMistakes = [
  {
    id: 1,
    question: 'Solve for x: 2x² + 5x - 3 = 0',
    yourAnswer: 'x = 1, x = -3',
    correctAnswer: 'x = 0.5, x = -3',
    subject: 'Mathematics',
    date: '2025-02-28',
    status: 'reviewed'
  },
  {
    id: 2,
    question: 'What is the powerhouse of the cell?',
    yourAnswer: 'Nucleus',
    correctAnswer: 'Mitochondria',
    subject: 'Science',
    date: '2025-02-27',
    status: 'reviewed'
  },
  {
    id: 3,
    question: 'Explain the process of photosynthesis',
    yourAnswer: 'Plants absorb sunlight...',
    correctAnswer: 'Plants convert light energy...',
    subject: 'Science',
    date: '2025-02-26',
    status: 'pending'
  },
];


export default function RevisionPage({ onPageChange }: RevisionPageProps) {
  const [notes, setNotes] = useState<Note[]>(defaultNotes);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteSubject, setNoteSubject] = useState('Math');
  const [noteDescription, setNoteDescription] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'collected' | 'papers' | 'mistakes'>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load saved notes from localStorage on mount
  useEffect(() => {
    const savedNotes = localStorage.getItem('revisionNotes');
    if (savedNotes) {
      try {
        const parsed = JSON.parse(savedNotes);
        setNotes([...defaultNotes, ...parsed]);
      } catch (e) {
        console.error('Failed to parse saved notes:', e);
      }
    }
  }, []);

  // Save notes to localStorage whenever custom notes change
  useEffect(() => {
    const customNotes = notes.filter(n => n.isCustom);
    localStorage.setItem('revisionNotes', JSON.stringify(customNotes));
  }, [notes]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const newFiles = Array.from(files).map(f => f.name);
      setUploadedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleSaveNote = () => {
    if (!noteTitle.trim()) return;

    const newNote: Note = {
      id: Date.now().toString(),
      subject: noteSubject,
      title: noteTitle,
      description: noteDescription || `Personal notes for ${noteSubject}`,
      color: noteSubject === 'Math' ? 'blue' : noteSubject === 'Science' ? 'emerald' : 'orange',
      updated: 'Just now',
      pages: uploadedFiles.length > 0 ? uploadedFiles.length : 1,
      isCustom: true,
      fileName: uploadedFiles[0]
    };

    setNotes(prev => [newNote, ...prev]);
    
    // Reset form
    setNoteTitle('');
    setNoteDescription('');
    setUploadedFiles([]);
    setIsUploadModalOpen(false);
  };

  const handleDeleteNote = (noteId: string) => {
    setNotes(prev => prev.filter(n => n.id !== noteId));
  };

  const displayedNotes = activeTab === 'all' 
    ? [...notes, ...dailyPapers]
    : activeTab === 'collected'
    ? notes.filter(n => n.isCustom)
    : dailyPapers;


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="revision-page"
    >
      <main className="page-content">
        {/* Hero Section */}
        <section className="hero-section">
          <motion.div 
            className="hero-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="hero-icon">
              <Sparkles size={32} />
            </div>
            <div className="hero-text">
              <h2>AI-Generated Study Materials</h2>
              <p>Personalized revision notes tailored to your learning style and curriculum</p>
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <span className="stat-num">{notes.length + dailyPapers.length}</span>
                <span className="stat-label">Notes</span>
              </div>
              <div className="hero-stat">
                <span className="stat-num">6</span>
                <span className="stat-label">Subjects</span>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Tabs and Upload Button */}
        <section className="notes-section">
          <div className="section-header">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="section-title">Your Notes</h2>
                <p className="section-subtitle">Recently updated study materials</p>
              </div>
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 mr-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-purple-500/30 hover:scale-105 transition-all duration-300 border border-purple-400/20"
              >
                <Upload size={18} />
                <span>Upload Notes</span>
              </button>

            </div>
            
            {/* Tabs */}
            <div className="flex gap-4 mt-4">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'all' 
                    ? 'bg-gray-900 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All Notes
              </button>
              <button
                onClick={() => setActiveTab('collected')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'collected' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                My Collection ({notes.filter(n => n.isCustom).length})
              </button>
              <button
                onClick={() => setActiveTab('mistakes')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'mistakes' 
                    ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <AlertCircle size={14} />
                Mistakes
                <span className="ml-1 px-1.5 py-0.5 bg-white text-red-500 text-xs rounded-full">{recentMistakes.length}</span>
              </button>


            </div>
          </div>

          {/* Notes Grid */}
          {activeTab !== 'mistakes' && (
          <div className="notes-grid">
            {displayedNotes.map((note, index) => {
              const SubjectIcon = subjectIcons[note.subject] || FileText;
              const isPaper = note.id.startsWith('paper-');
              return (
                <motion.div
                  key={note.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + index * 0.08 }}
                  className={`note-card ${note.color} ${note.isCustom ? 'custom-note' : ''} ${isPaper ? 'paper-note' : ''}`}
                >
                  <div className="card-glow" />

                  <div className="card-header">
                    <div className="header-left">
                      <div className="subject-icon-wrapper">
                        <SubjectIcon size={20} />
                      </div>
                      <span className="subject-name">{note.subject}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {note.isCustom && (
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                      <div className="ai-indicator">
                        {isPaper ? (
                          <>
                            <Sparkles size={12} />
                            <span>Daily Rec</span>
                          </>
                        ) : note.isCustom ? (
                          <>
                            <Upload size={12} />
                            <span>My Note</span>
                          </>
                        ) : (
                          <>
                            <Lightbulb size={12} />
                            <span>AI</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="card-body">
                    <h3 className="note-title">{note.title}</h3>
                    <p className="note-description">{note.description}</p>
                  </div>

                  <div className="card-footer">
                    <div className="footer-meta">
                      <span className="meta-item">
                        <FileText size={14} />
                        {note.pages} pages
                      </span>
                      <span className="meta-item">
                        <Clock size={14} />
                        {note.updated}
                      </span>
                    </div>
                    
                    <button className="open-btn">
                      <span>Open</span>
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
          )}

          {/* Mistakes Section */}
          {activeTab === 'mistakes' && (
            <div className="mistakes-section">
              {/* Progress Hero */}
              <motion.div
                className="hero-card mb-8"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="hero-icon">
                  <Target size={32} />
                </div>
                <div className="hero-text">
                  <h2>Your Mistakes</h2>
                  <p>Track and review your errors to improve learning</p>
                </div>
                <div className="hero-stats">
                  <div className="hero-stat">
                    <span className="stat-num">{recentMistakes.filter(m => m.status === 'reviewed').length}</span>
                    <span className="stat-label">Reviewed</span>
                  </div>
                  <div className="hero-stat">
                    <span className="stat-num">{recentMistakes.filter(m => m.status === 'pending').length}</span>
                    <span className="stat-label">Pending</span>
                  </div>
                </div>
              </motion.div>

              {/* Mistakes List */}
              <div className="mistakes-list">
                {recentMistakes.map((mistake, index) => (
                  <motion.div
                    key={mistake.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + index * 0.1 }}
                    className="mistake-item bg-white rounded-xl p-6 mb-4 shadow-sm border border-gray-100"
                  >
                    <div className="flex items-start gap-4">
                      <div className="mt-1">
                        {mistake.status === 'reviewed' ? (
                          <CheckCircle className="text-green-500" size={20} />
                        ) : (
                          <AlertCircle className="text-orange-500" size={20} />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-2">{mistake.question}</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500">Your answer:</span>
                            <span className="text-red-600 line-through">{mistake.yourAnswer}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500">Correct:</span>
                            <span className="text-green-600 font-medium">{mistake.correctAnswer}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                          <span>{mistake.subject}</span>
                          <span>{mistake.date}</span>
                        </div>
                      </div>
                      <button className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors">
                        {mistake.status === 'reviewed' ? 'Review Again' : 'Review'}
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

        </section>
      </main>

      {/* Upload Modal */}
      <AnimatePresence>
        {isUploadModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setIsUploadModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden"
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Upload Notes</h3>
                  <p className="text-sm text-gray-500">Add your personal study materials</p>
                </div>
                <button 
                  onClick={() => setIsUploadModalOpen(false)}
                  className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-4">
                {/* Title Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Note Title</label>
                  <input
                    type="text"
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    placeholder="e.g., Math Chapter 5 Notes"
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none"
                  />
                </div>

                {/* Subject Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                  <select
                    value={noteSubject}
                    onChange={(e) => setNoteSubject(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none"
                  >
                    <option value="Math">Mathematics</option>
                    <option value="Science">Science</option>
                    <option value="History">History</option>
                    <option value="English">English</option>
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                  <textarea
                    value={noteDescription}
                    onChange={(e) => setNoteDescription(e.target.value)}
                    placeholder="Brief description of your notes..."
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none resize-none"
                  />
                </div>

                {/* Upload Area */}
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-200 rounded-2xl p-6 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/30 transition-all"
                >
                  <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-purple-100 flex items-center justify-center">
                    <Upload className="text-purple-600" size={24} />
                  </div>
                  <p className="text-gray-900 font-medium text-sm">Click to upload files</p>
                  <p className="text-xs text-gray-500 mt-1">PDF, DOC, images</p>
                </div>
                <input 
                  ref={fileInputRef}
                  type="file" 
                  multiple 
                  accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                  className="hidden" 
                  onChange={handleFileUpload}
                />

                {/* Uploaded Files */}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-700">Uploaded files:</p>
                    {uploadedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 p-2 bg-green-50 rounded-lg"
                      >
                        <CheckCircle className="text-green-600" size={16} />
                        <span className="flex-1 text-sm text-gray-700 truncate">{file}</span>
                        <button 
                          onClick={() => setUploadedFiles(prev => prev.filter((_, i) => i !== index))}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 bg-gray-50 flex gap-3">
                <button 
                  onClick={() => setIsUploadModalOpen(false)}
                  className="flex-1 py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleSaveNote}
                  disabled={!noteTitle.trim()}
                  className="flex-1 py-3 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Save to Collection
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

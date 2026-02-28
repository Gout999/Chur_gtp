import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Users, 
  BookOpen, 
  Clock, 
  X,
  CheckCircle,
  Download,
  Sparkles,
  FileText,
  GraduationCap
} from 'lucide-react';
import type { PageType } from '@/types';


interface ClassesPageProps {
  onPageChange: (_page: PageType) => void;
}

interface ClassData {
  id: string;
  name: string;
  subject: string;
  students: number;
  schedule: string;
  color: string;
  notesCount: number;
}

interface EnhancedNote {
  id: string;
  originalName: string;
  enhancedName: string;
  subject: string;
  uploadDate: string;
  downloadUrl: string;
}

const mockClasses: ClassData[] = [
  { 
    id: '1', 
    name: 'Form 4A - Mathematics', 
    subject: 'Mathematics', 
    students: 32, 
    schedule: 'Mon, Wed 10:00 AM',
    color: 'from-blue-500/20 to-blue-600/10',
    notesCount: 12
  },
  { 
    id: '2', 
    name: 'Form 5B - Physics', 
    subject: 'Physics', 
    students: 28, 
    schedule: 'Tue, Thu 2:00 PM',
    color: 'from-emerald-500/20 to-emerald-600/10',
    notesCount: 8
  },
  { 
    id: '3', 
    name: 'Form 3C - Chemistry', 
    subject: 'Chemistry', 
    students: 35, 
    schedule: 'Mon, Fri 11:30 AM',
    color: 'from-purple-500/20 to-purple-600/10',
    notesCount: 15
  },
  { 
    id: '4', 
    name: 'Form 6 - Biology', 
    subject: 'Biology', 
    students: 24, 
    schedule: 'Wed, Thu 9:00 AM',
    color: 'from-orange-500/20 to-orange-600/10',
    notesCount: 6
  },
];

// Mock database of AI-enhanced notes
const mockEnhancedNotes: EnhancedNote[] = [
  {
    id: '1',
    originalName: 'Math_Chapter5_Notes.pdf',
    enhancedName: 'Math_Chapter5_AI_Enhanced.pdf',
    subject: 'Mathematics',
    uploadDate: '2025-02-28',
    downloadUrl: '/downloads/math_chapter5_enhanced.pdf'
  },
  {
    id: '2',
    originalName: 'Physics_Lab_Report.docx',
    enhancedName: 'Physics_Lab_Report_AI_Enhanced.pdf',
    subject: 'Physics',
    uploadDate: '2025-02-27',
    downloadUrl: '/downloads/physics_lab_enhanced.pdf'
  },
  {
    id: '3',
    originalName: 'Chemistry_Formulas.pdf',
    enhancedName: 'Chemistry_Formulas_AI_Enhanced.pdf',
    subject: 'Chemistry',
    uploadDate: '2025-02-26',
    downloadUrl: '/downloads/chemistry_formulas_enhanced.pdf'
  },
];

export default function ClassesPage({ onPageChange }: ClassesPageProps) {
  const [selectedClass, setSelectedClass] = useState<ClassData | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [enhancedNotes] = useState<EnhancedNote[]>(mockEnhancedNotes);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClassClick = (classData: ClassData) => {
    setSelectedClass(classData);
    setIsUploadModalOpen(true);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const newFiles = Array.from(files).map(f => f.name);
      setUploadedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleUpload = () => {
    setIsUploadModalOpen(false);
    setUploadedFiles([]);
    onPageChange('ai-enhancement-editor');
  };
  const handleDownload = (note: EnhancedNote) => {
    // Simulate file download
    const link = document.createElement('a');
    link.href = note.downloadUrl;
    link.download = note.enhancedName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="min-h-screen bg-gray-50/50 pt-20"
    >
      {/* Header - Page Title with icon */}
      <div className="max-w-[1600px] mx-auto px-6 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Class Management</h1>
              <p className="text-sm text-gray-500">Manage your classes, upload course materials, and view AI-enhanced notes</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {mockClasses.map((classData, index) => (
            <motion.div
              key={classData.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => handleClassClick(classData)}
              className="group relative bg-white rounded-2xl p-6 shadow-sm border border-gray-100 cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
            >
              {/* Gradient Background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${classData.color} opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-300`} />
              
              <div className="relative">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center text-2xl">
                      {classData.subject === 'Mathematics' && '🔢'}
                      {classData.subject === 'Physics' && '⚡'}
                      {classData.subject === 'Chemistry' && '🧪'}
                      {classData.subject === 'Biology' && '🧬'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 group-hover:text-gray-900">{classData.name}</h3>
                      <span className="text-sm text-gray-500">{classData.subject}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-amber-500">
                    <BookOpen size={16} />
                    <span className="text-sm font-medium">{classData.notesCount}</span>
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-6 text-sm text-gray-500">
                  <div className="flex items-center gap-2">
                    <Users size={16} />
                    <span>{classData.students} students</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={16} />
                    <span>{classData.schedule}</span>
                  </div>
                </div>

                {/* Upload Action */}
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 transition-all duration-300">
                    <Upload size={16} />
                    Upload Notes
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* AI Enhanced Notes Section */}
        <div className="mt-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900">AI Enhanced Notes</h3>
              <p className="text-sm text-gray-500 mt-1">Download AI-improved versions of your uploaded notes</p>
            </div>
            <button
              onClick={() => setIsDownloadModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all"
            >
              <Download size={18} />
              <span>View Enhanced Notes</span>
            </button>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <AnimatePresence>
        {isUploadModalOpen && selectedClass && (
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
                  <p className="text-sm text-gray-500">{selectedClass.name}</p>
                </div>
                <button 
                  onClick={() => setIsUploadModalOpen(false)}
                  className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Upload Area */}
              <div className="p-6">
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/30 transition-all"
                >
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 flex items-center justify-center">
                    <Upload className="text-purple-600" size={28} />
                  </div>
                  <p className="text-gray-900 font-medium mb-1">Click to upload files</p>
                  <p className="text-sm text-gray-500">or drag and drop</p>
                  <p className="text-xs text-gray-400 mt-2">PDF, DOC, DOCX up to 10MB</p>
                </div>
                <input 
                  ref={fileInputRef}
                  type="file" 
                  multiple 
                  accept=".pdf,.doc,.docx"
                  className="hidden" 
                  onChange={handleFileUpload}
                />

                {/* Uploaded Files */}
                {uploadedFiles.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-4 space-y-2"
                  >
                    <p className="text-sm font-medium text-gray-700 mb-2">Uploaded files:</p>
                    {uploadedFiles.map((file, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center gap-3 p-3 bg-green-50 rounded-xl"
                      >
                        <CheckCircle className="text-green-600" size={18} />
                        <span className="flex-1 text-sm text-gray-700 truncate">{file}</span>
                        <button 
                          onClick={() => setUploadedFiles(prev => prev.filter((_, i) => i !== index))}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <X size={16} />
                        </button>
                      </motion.div>
                    ))}
                  </motion.div>
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
                  onClick={handleUpload}
                  disabled={uploadedFiles.length === 0}
                  className="flex-1 py-3 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Upload {uploadedFiles.length > 0 && `(${uploadedFiles.length})`}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success Modal */}
      <AnimatePresence>
        {isSuccessModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setIsSuccessModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden text-center p-8"
            >
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="text-green-600" size={40} />
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Upload Successful!</h3>
              <p className="text-gray-500 mb-6">
                Your notes have been uploaded successfully. AI is now processing and enhancing your notes.
              </p>
              
              <div className="bg-purple-50 rounded-xl p-4 mb-6">
                <div className="flex items-center gap-2 text-purple-700 mb-2">
                  <Sparkles size={20} />
                  <span className="font-semibold">AI Enhancement in Progress</span>
                </div>
                <p className="text-sm text-purple-600">
                  The enhanced version will be available for download in a few minutes.
                </p>
              </div>
              
              <button 
                onClick={() => setIsSuccessModalOpen(false)}
                className="w-full py-3 rounded-xl bg-gray-900 text-white font-medium hover:bg-gray-800 transition-colors"
              >
                Got it!
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Download AI Enhanced Notes Modal */}
      <AnimatePresence>
        {isDownloadModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setIsDownloadModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden max-h-[80vh] flex flex-col"
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">AI Enhanced Notes</h3>
                  <p className="text-sm text-gray-500">Download improved versions of your notes</p>
                </div>
                <button 
                  onClick={() => setIsDownloadModalOpen(false)}
                  className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Notes List */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="space-y-3">
                  {enhancedNotes.map((note, index) => (
                    <motion.div
                      key={note.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                        <FileText className="text-purple-600" size={20} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-500 mb-1">Original: {note.originalName}</p>
                        <h4 className="font-medium text-gray-900 truncate">{note.enhancedName}</h4>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">{note.subject}</span>
                          <span>Uploaded: {note.uploadDate}</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => handleDownload(note)}
                        className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                      >
                        <Download size={16} />
                        Download
                      </button>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                <button 
                  onClick={() => setIsDownloadModalOpen(false)}
                  className="w-full py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles,
  BookOpen,
  Brain,
  Lightbulb,
  HelpCircle,
  Image as ImageIcon,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  GraduationCap,
  Users,
  Target,
  FileText,
  BarChart3,
  Check,
  Loader2
} from 'lucide-react';
import type { PageType } from '@/types';

interface AIEnhancementEditorProps {
  onPageChange: (_page: PageType) => void;
}

interface EnhancementSettings {
  difficulty: 'elementary' | 'intermediate' | 'advanced' | 'expert';
  enhancements: string[];
  targetAudience: 'beginners' | 'average' | 'advanced_students' | 'mixed';
  includeVisuals: boolean;
  generateQuiz: boolean;
  addKeyPoints: boolean;
  languageStyle: 'academic' | 'casual' | 'professional';
  expandContent: boolean;
  focusAreas: string[];
}

const enhancementOptions = [
  { value: 'summary', label: 'AI Smart Summary', icon: Sparkles, description: 'Auto-generate content summary' },
  { value: 'questions', label: 'Practice Questions', icon: HelpCircle, description: 'Generate practice questions from content' },
  { value: 'visual', label: 'Visual Aids', icon: ImageIcon, description: 'Add charts and diagrams' },
  { value: 'examples', label: 'Examples', icon: Lightbulb, description: 'Add real-world application examples' },
  { value: 'simplified', label: 'Simplified Content', icon: BookOpen, description: 'Simplify complex concepts' },
  { value: 'extended', label: 'Extended Content', icon: FileText, description: 'Add extra related knowledge' },
];

const focusAreaOptions = [
  'Core Concepts',
  'Application Skills',
  'Exam Focus',
  'Common Mistakes',
  'Advanced Topics',
  'Practical Use',
];

const steps = ['Select Enhancement', 'Set Target Audience', 'Adjust Options', 'Preview & Confirm'];

export default function AIEnhancementEditor({ onPageChange }: AIEnhancementEditorProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [settings, setSettings] = useState<EnhancementSettings>({
    difficulty: 'intermediate',
    enhancements: ['summary', 'questions'],
    targetAudience: 'mixed',
    includeVisuals: true,
    generateQuiz: true,
    addKeyPoints: true,
    languageStyle: 'academic',
    expandContent: false,
    focusAreas: ['Core Concepts', 'Exam Focus'],
  });

  const handleSettingChange = useCallback(<K extends keyof EnhancementSettings>(
    key: K,
    value: EnhancementSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const toggleEnhancement = useCallback((value: string) => {
    setSettings(prev => ({
      ...prev,
      enhancements: prev.enhancements.includes(value)
        ? prev.enhancements.filter(e => e !== value)
        : [...prev.enhancements, value],
    }));
  }, []);

  const toggleFocusArea = useCallback((area: string) => {
    setSettings(prev => ({
      ...prev,
      focusAreas: prev.focusAreas.includes(area)
        ? prev.focusAreas.filter(a => a !== area)
        : [...prev.focusAreas, area],
    }));
  }, []);

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      handleGenerate();
    } else {
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleGenerate = async () => {
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsProcessing(false);
    setShowSuccess(true);
  };

  const handleFinish = () => {
    onPageChange('teacher-classes');
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                Select AI Enhancement Features
              </h3>
              <p className="text-sm text-gray-500">
                Choose the types of AI enhancements you want to apply to your course materials. You can select multiple options.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {enhancementOptions.map((option) => {
                const Icon = option.icon;
                const isSelected = settings.enhancements.includes(option.value);
                return (
                  <motion.div
                    key={option.value}
                    onClick={() => toggleEnhancement(option.value)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-purple-500 bg-purple-50' 
                        : 'border-gray-200 hover:border-purple-300 hover:shadow-md'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${
                      isSelected ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-500'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <h4 className="font-medium text-gray-900 mb-1">{option.label}</h4>
                    <p className="text-xs text-gray-500">{option.description}</p>
                  </motion.div>
                );
              })}
            </div>

            <div className="pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-4">Difficulty Level</h4>
              <div className="space-y-4">
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="1"
                  value={['elementary', 'intermediate', 'advanced', 'expert'].indexOf(settings.difficulty)}
                  onChange={(e) => {
                    const levels: Array<EnhancementSettings['difficulty']> = ['elementary', 'intermediate', 'advanced', 'expert'];
                    handleSettingChange('difficulty', levels[parseInt(e.target.value)]);
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                />
                <div className="flex justify-between text-sm">
                  <span className={settings.difficulty === 'elementary' ? 'text-purple-600 font-medium' : 'text-gray-500'}>Elementary</span>
                  <span className={settings.difficulty === 'intermediate' ? 'text-purple-600 font-medium' : 'text-gray-500'}>Intermediate</span>
                  <span className={settings.difficulty === 'advanced' ? 'text-purple-600 font-medium' : 'text-gray-500'}>Advanced</span>
                  <span className={settings.difficulty === 'expert' ? 'text-purple-600 font-medium' : 'text-gray-500'}>Expert</span>
                </div>
              </div>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-purple-600" />
                Set Target Audience
              </h3>
              <p className="text-sm text-gray-500">
                Choose the main target student group for these enhanced notes.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { value: 'beginners', label: 'Beginners', desc: 'Suitable for students just starting out', icon: BookOpen },
                { value: 'average', label: 'Average Students', desc: 'Students with basic knowledge', icon: Users },
                { value: 'advanced_students', label: 'Advanced Students', desc: 'Students needing challenging content', icon: Brain },
                { value: 'mixed', label: 'Mixed Level', desc: 'Suitable for various skill levels', icon: Target },
              ].map((audience) => {
                const Icon = audience.icon;
                const isSelected = settings.targetAudience === audience.value;
                return (
                  <motion.div
                    key={audience.value}
                    onClick={() => handleSettingChange('targetAudience', audience.value as EnhancementSettings['targetAudience'])}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-purple-500 bg-purple-50' 
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isSelected ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-500'
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">{audience.label}</h4>
                        <p className="text-xs text-gray-500">{audience.desc}</p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-600" />
                Detailed Options
              </h3>
              <p className="text-sm text-gray-500">
                Further customize the specific AI enhancement options.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 bg-gray-50 rounded-xl">
                <h4 className="font-medium text-gray-900 mb-3">Focus Areas</h4>
                <div className="flex flex-wrap gap-2">
                  {focusAreaOptions.map((area) => (
                    <button
                      key={area}
                      onClick={() => toggleFocusArea(area)}
                      className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                        settings.focusAreas.includes(area)
                          ? 'bg-purple-600 text-white'
                          : 'bg-white text-gray-600 border border-gray-200 hover:border-purple-300'
                      }`}
                    >
                      {area}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl">
                <h4 className="font-medium text-gray-900 mb-3">Language Style</h4>
                <select
                  value={settings.languageStyle}
                  onChange={(e) => handleSettingChange('languageStyle', e.target.value as EnhancementSettings['languageStyle'])}
                  className="w-full p-2.5 rounded-lg border border-gray-200 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="academic">Academic</option>
                  <option value="casual">Casual & Easy</option>
                  <option value="professional">Professional</option>
                </select>
              </div>

              <div className="md:col-span-2 p-4 bg-gray-50 rounded-xl">
                <h4 className="font-medium text-gray-900 mb-3">Other Options</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { key: 'includeVisuals', label: 'Include Visual Aids' },
                    { key: 'generateQuiz', label: 'Generate Quiz Questions' },
                    { key: 'addKeyPoints', label: 'Highlight Key Points' },
                    { key: 'expandContent', label: 'Expand Content' },
                  ].map((option) => (
                    <label key={option.key} className="flex items-center gap-3 p-3 bg-white rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                      <input
                        type="checkbox"
                        checked={settings[option.key as keyof EnhancementSettings] as boolean}
                        onChange={(e) => handleSettingChange(option.key as keyof EnhancementSettings, e.target.checked)}
                        className="w-4 h-4 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                      />
                      <span className="text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-600" />
                Preview Settings
              </h3>
              <p className="text-sm text-gray-500">
                Confirm your AI enhancement settings before generating.
              </p>
            </div>
            
            <div className="bg-gray-50 rounded-xl p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">AI Enhancement Features</h4>
                  <div className="flex flex-wrap gap-2">
                    {settings.enhancements.map(e => {
                      const option = enhancementOptions.find(o => o.value === e);
                      return (
                        <span key={e} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                          {option?.label}
                        </span>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Difficulty Level</h4>
                  <p className="text-sm text-gray-900 capitalize">
                    {settings.difficulty}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Target Audience</h4>
                  <p className="text-sm text-gray-900 capitalize">
                    {settings.targetAudience.replace('_', ' ')}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Language Style</h4>
                  <p className="text-sm text-gray-900 capitalize">
                    {settings.languageStyle}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Focus Areas</h4>
                  <div className="flex flex-wrap gap-1">
                    {settings.focusAreas.map(area => (
                      <span key={area} className="text-xs text-gray-600">• {area}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Other Options</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    {settings.includeVisuals && <div>✓ Include Visual Aids</div>}
                    {settings.generateQuiz && <div>✓ Generate Quiz Questions</div>}
                    {settings.addKeyPoints && <div>✓ Highlight Key Points</div>}
                    {settings.expandContent && <div>✓ Expand Content</div>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (showSuccess) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="min-h-screen bg-gray-50/50 flex items-center justify-center p-4"
      >
        <div className="max-w-md w-full">
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl shadow-xl p-8 text-center"
          >
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Enhancement Complete!</h2>
            <p className="text-gray-500 mb-6">
              AI has successfully generated enhanced notes based on your settings. Students can now view and download these notes from their course page.
            </p>
            
            <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left">
              <h4 className="font-medium text-gray-900 mb-2">Generation Summary:</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <div>• Enhancement Types: {settings.enhancements.map(e => enhancementOptions.find(o => o.value === e)?.label).join(', ')}</div>
                <div>• Difficulty: {settings.difficulty}</div>
                <div>• Target Audience: {settings.targetAudience.replace('_', ' ')}</div>
                <div>• Focus Areas: {settings.focusAreas.join(', ')}</div>
              </div>
            </div>
            
            <button
              onClick={handleFinish}
              className="w-full py-3 rounded-xl bg-gray-900 text-white font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Classes
            </button>
          </motion.div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-gray-50/50 py-8 px-4"
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">AI Enhancement Editor</h1>
          </div>
          <p className="text-gray-500 ml-13">
            Customize how AI enhances your course materials to generate personalized learning materials for students
          </p>
        </div>

        {/* Stepper */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                    index <= activeStep 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-gray-200 text-gray-500'
                  }`}>
                    {index < activeStep ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span className={`text-xs mt-2 ${index <= activeStep ? 'text-purple-600' : 'text-gray-400'}`}>
                    {step}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 sm:w-24 h-0.5 mx-2 ${
                    index < activeStep ? 'bg-purple-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <motion.div
          key={activeStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6"
        >
          {getStepContent(activeStep)}
        </motion.div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={handleBack}
            disabled={activeStep === 0 || isProcessing}
            className="px-6 py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <button
            onClick={handleNext}
            disabled={isProcessing || settings.enhancements.length === 0}
            className="px-6 py-3 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : activeStep === steps.length - 1 ? (
              <>
                Start Generation
                <CheckCircle className="w-4 h-4" />
              </>
            ) : (
              <>
                Next
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

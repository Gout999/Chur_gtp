export type PageType = 'intro' | 'home' | 'dashboard' | 'classes' | 'teacher-dashboard' | 'teacher-classes' | 'teacher-assignments' | 'teacher-analytics' | 'revision' | 'homework' | 'mistakes' | 'daily-recommendation' | 'assignments' | 'ai-enhancement-editor';

export interface NavItem {
  label: string;
  href: string;
  page: PageType;
}

export interface FeatureCardData {
  title: string;
  description: string;
  icon: string;
}

export interface CaseStudy {
  id: number;
  title: string;
  image: string;
  category: string;
}

export interface CarouselImage {
  id: number;
  src: string;
  alt: string;
}

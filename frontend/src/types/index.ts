export type PageType = 'home' | 'dashboard' | 'revision' | 'homework' | 'mistakes';

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

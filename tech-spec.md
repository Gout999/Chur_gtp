# Charles Elena 网站技术规划

## 1. 组件清单

### shadcn/ui 组件
- Button - 按钮组件
- Card - 卡片组件
- NavigationMenu - 导航菜单
- DropdownMenu - 下拉菜单

### 自定义组件

| 组件名 | 用途 | 位置 |
|--------|------|------|
| `Navbar` | 顶部导航栏 | `src/components/Navbar.tsx` |
| `HeroSection` | 首页四分栏 | `src/sections/HeroSection.tsx` |
| `SplitColumn` | 单个分栏组件 | `src/components/SplitColumn.tsx` |
| `DelightPage` | Delight 页面 | `src/sections/DelightPage.tsx` |
| `ExperiencePage` | Experience 页面 | `src/sections/ExperiencePage.tsx` |
| `FeatureCard` | 特色卡片 | `src/components/FeatureCard.tsx` |
| `CaseStudyGrid` | 案例网格 | `src/components/CaseStudyGrid.tsx` |
| `BackgroundCarousel` | 背景轮播 | `src/components/BackgroundCarousel.tsx` |
| `PageTransition` | 页面切换动画 | `src/components/PageTransition.tsx` |
| `ScrollReveal` | 滚动显示动画 | `src/components/ScrollReveal.tsx` |

## 2. 动画实现方案

| 动画 | 库 | 实现方式 | 复杂度 |
|------|-----|----------|--------|
| 分栏悬停扩展 | Framer Motion | `layout` + `animate` 属性 | 高 |
| 页面切换滑动 | Framer Motion | `AnimatePresence` + `motion.div` | 高 |
| 背景视频/图片缩放 | CSS/Framer | `scale` transform | 低 |
| 滚动触发显示 | Framer Motion | `whileInView` + `viewport` | 中 |
| 导航栏背景变化 | React State | 监听滚动事件，切换 class | 低 |
| 按钮悬停效果 | Tailwind/CSS | `hover:` 类 + transition | 低 |
| 卡片悬停上浮 | Tailwind/CSS | `hover:translate-y` + shadow | 低 |
| 背景轮播切换 | Framer Motion | `AnimatePresence` + 淡入淡出 | 中 |
| 文字 stagger 动画 | Framer Motion | `staggerChildren` + `delayChildren` | 中 |

## 3. 项目结构

```
src/
├── components/
│   ├── Navbar.tsx
│   ├── SplitColumn.tsx
│   ├── FeatureCard.tsx
│   ├── CaseStudyGrid.tsx
│   ├── BackgroundCarousel.tsx
│   ├── PageTransition.tsx
│   └── ScrollReveal.tsx
├── sections/
│   ├── HeroSection.tsx
│   ├── DelightPage.tsx
│   └── ExperiencePage.tsx
├── hooks/
│   └── useScrollPosition.ts
├── pages/
│   └── Index.tsx
├── App.tsx
├── main.tsx
└── index.css
```

## 4. 依赖安装

```bash
# 动画库
npm install framer-motion

# 图标库
npm install lucide-react

# 工具库
npm install clsx tailwind-merge
```

## 5. 状态管理

使用 React Context 管理全局状态：
- `currentPage`: 当前页面 ('home' | 'delight' | 'experience' | 'create' | 'grow')
- `isNavVisible`: 导航栏是否可见
- `scrollPosition`: 滚动位置

## 6. 路由方案

使用状态驱动路由（无需 react-router）：
- URL hash 变化触发页面切换
- `#/` - 首页
- `#/delight` - Delight 页面
- `#/experience` - Experience 页面
- `#/create` - Create 页面
- `#/grow` - Grow 页面

## 7. 性能优化

- 视频使用 `preload="none"` 延迟加载
- 图片使用懒加载
- 动画使用 `will-change` 优化
- 使用 `requestAnimationFrame` 处理滚动事件

## 8. 响应式断点

```css
/* Tailwind 默认断点 */
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
```

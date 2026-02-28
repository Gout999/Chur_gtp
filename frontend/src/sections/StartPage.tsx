import { useState, useEffect, useRef, useCallback } from 'react'
import './StartPage.css';
import type { PageType } from '@/types';
import { Search, Menu, Layers, Grid3X3 } from 'lucide-react'

interface FloatingObject {
  id: number
  image: string
  x: number
  y: number
  z: number
  baseX: number
  baseY: number
  size: number
  rotation: number
  rotationSpeed: number
  speed: number
}

const educationalImages = [
  '/assets/picture/098182f29c60f84d2db5c72c7190fb58.png',
  '/assets/picture/0e83da753f7fe80038dfb5fc9def8a10.png',
  '/assets/picture/32b58dd17aad594934f61cdcc4c49407.png',
  '/assets/picture/4c759442ae8486875b4c3303cc0b9a17.png',
  '/assets/picture/52ad4490f8be7c81cb513e7c36f4565a.png',
  '/assets/picture/6ae446336571030d36e80d28ae1bfff0.png',
  '/assets/picture/709235e9a772426b94763e9ac5d3f384.png',
  '/assets/picture/c7836d434605eac8adc940493504637d.png',
  '/assets/picture/d0c77fe6521474e525424fdaf58fc9f1.png',
  '/assets/picture/d57469949aeaedbf6c7677c7e0ef35f3.png',
  '/assets/picture/098182f29c60f84d2db5c72c7190fb58.png',
  '/assets/picture/0e83da753f7fe80038dfb5fc9def8a10.png',
  '/assets/picture/32b58dd17aad594934f61cdcc4c49407.png',
]

const SPAWN_Z = -3000
const RESET_Z = 500
const DEFAULT_SPEED = 150

// Dashboard images to preload during transition
const STUDENT_DASHBOARD_IMAGES = [
  '/images/revision-bg.jpg',
  '/images/homework-bg.jpg',
  '/images/mistakes-bg.jpg',
]

const TEACHER_DASHBOARD_IMAGES = [
  '/images/revision-bg.jpg',
  '/images/homework-bg.jpg',
  '/images/teacher-analytics-bg.jpg',
]

// Preload images in background
const preloadImages = (images: string[]) => {
  images.forEach(src => {
    const img = new Image()
    img.src = src
    // No need to wait, just start loading in background
  })
}

type TransitionPhase = 'idle' | 'zooming' | 'showName' | 'complete'

interface StartPageProps {
  onPageChange: (page: PageType) => void;
}

export default function StartPage({ onPageChange }: StartPageProps) {
  const [objects, setObjects] = useState<FloatingObject[]>([])
  const [hoveredObject, setHoveredObject] = useState<number | null>(null)
  const [transitionPhase, setTransitionPhase] = useState<TransitionPhase>('idle')
  const [cameraZ, setCameraZ] = useState(0)
  const [whiteOpacity, setWhiteOpacity] = useState(0)
  const [nameOpacity, setNameOpacity] = useState(0)
  const [startPageOpacity] = useState(1)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const targetSpeedRef = useRef(1)
  const currentSpeedRef = useRef(1)
  const transitionStartTime = useRef<number | null>(null)
  const transitionTargetRef = useRef<PageType>('dashboard')
  const hasCalledPageChange = useRef(false)

  useEffect(() => {
    const initialObjects: FloatingObject[] = educationalImages.map((image, index) => {
      const zSpacing = 250
      const initialZ = SPAWN_Z + (index * zSpacing) + Math.random() * 100
      const angle = Math.random() * Math.PI * 2
      const radius = 100 + Math.random() * 300
      
      return {
        id: index,
        image,
        x: 0,
        y: 0,
        z: initialZ,
        baseX: Math.cos(angle) * radius,
        baseY: Math.sin(angle) * radius * 0.6,
        size: 110 + Math.random() * 88,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 0.2,
        speed: DEFAULT_SPEED + Math.random() * 50,
      }
    })
    setObjects(initialObjects)
  }, [])

  const handleWheel = useCallback((e: WheelEvent) => {
    if (transitionPhase !== 'idle') {
      e.preventDefault()
      return
    }
    e.preventDefault()
    
    const delta = e.deltaY
    targetSpeedRef.current += delta * 0.01
    targetSpeedRef.current = Math.max(-2, Math.min(5, targetSpeedRef.current))
  }, [transitionPhase])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('wheel', handleWheel, { passive: false })
    
    return () => {
      container.removeEventListener('wheel', handleWheel)
    }
  }, [handleWheel])

  const studentTransition = useCallback(() => {
    if (transitionPhase !== 'idle') return
    hasCalledPageChange.current = false
    transitionTargetRef.current = 'dashboard'
    
    // Start preloading dashboard images immediately when transition begins
    preloadImages(STUDENT_DASHBOARD_IMAGES)
    
    setTransitionPhase('zooming')
    transitionStartTime.current = performance.now()
  }, [transitionPhase])

  const teacherTransition = useCallback(() => {
    if (transitionPhase !== 'idle') return
    hasCalledPageChange.current = false
    transitionTargetRef.current = 'teacher-dashboard'
    
    // Start preloading teacher dashboard images immediately when transition begins
    preloadImages(TEACHER_DASHBOARD_IMAGES)
    
    setTransitionPhase('zooming')
    transitionStartTime.current = performance.now()
  }, [transitionPhase])

  useEffect(() => {
    let lastTime = performance.now()
    
    const animate = (time: number) => {
      const deltaTime = (time - lastTime) / 1000
      lastTime = time
      
      if (transitionPhase === 'zooming') {
        const elapsed = time - (transitionStartTime.current || time)
        const progress = Math.min(elapsed / 1900, 1)
        
        const targetCameraZ = -2500
        const newCameraZ = targetCameraZ * easeInOutCubic(progress)
        setCameraZ(newCameraZ)
        
        targetSpeedRef.current = 0.2
        
        if (progress >= 1) {
          setTransitionPhase('showName')
          transitionStartTime.current = time
        }
      } else if (transitionPhase === 'showName') {
        const elapsed = time - (transitionStartTime.current || time)
        
        if (elapsed < 200) {
          setWhiteOpacity(elapsed / 200)
        } else {
          setWhiteOpacity(1)
        }
        
        if (elapsed < 300) {
          setNameOpacity(elapsed / 300)
        } else if (elapsed > 1500) {
          setNameOpacity(Math.max(0, 1 - (elapsed - 1500) / 500))
        } else {
          setNameOpacity(1)
        }
        
        if (elapsed > 2000) {
          // Direct transition to dashboard without circleExpand
          onPageChange(transitionTargetRef.current)
          setTransitionPhase('complete')
        }
      }
      
      if (transitionPhase !== 'complete') {
        const speedDiff = targetSpeedRef.current - currentSpeedRef.current
        currentSpeedRef.current += speedDiff * 3 * deltaTime
        
        setObjects(prevObjects => 
          prevObjects.map((obj) => {
            const moveSpeed = obj.speed * currentSpeedRef.current
            let newZ = obj.z + moveSpeed * deltaTime
            
            if (newZ > RESET_Z) {
              newZ = SPAWN_Z + Math.random() * 200
            }
            if (newZ < SPAWN_Z - 500) {
              newZ = RESET_Z - Math.random() * 200
            }
            
            const newRotation = obj.rotation + obj.rotationSpeed * (1 + Math.abs(currentSpeedRef.current - 1) * 0.5)
            
            return {
              ...obj,
              z: newZ,
              rotation: newRotation,
              x: obj.baseX,
              y: obj.baseY,
            }
          })
        )
      }
      
      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animationFrameRef.current = requestAnimationFrame(animate)
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [transitionPhase, onPageChange])

  const easeInOutCubic = (t: number) => {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
  }

  const getObjectStyle = (obj: FloatingObject) => {
    const perspective = 600
    const effectiveZ = obj.z - cameraZ
    const distance = perspective - effectiveZ
    const scale = perspective / Math.max(50, distance)
    
    let opacity = 1
    if (effectiveZ < -2500) {
      opacity = Math.max(0, 1 - (Math.abs(effectiveZ) - 2500) / 500)
    } else if (effectiveZ > 300) {
      opacity = Math.max(0, 1 - (effectiveZ - 300) / 200)
    }
    
    const focusZ = -500
    const distanceFromFocus = Math.abs(effectiveZ - focusZ)
    const blur = Math.min(8, distanceFromFocus / 400)
    
    const isHovered = hoveredObject === obj.id
    const hoverScale = isHovered ? 1.2 : 1
    
    const screenX = obj.x * scale
    const screenY = obj.y * scale
    
    return {
      position: 'absolute' as const,
      left: `calc(50% + ${screenX}px)`,
      top: `calc(50% + ${screenY}px)`,
      width: `${obj.size}px`,
      height: `${obj.size}px`,
      transform: `
        translate(-50%, -50%)
        scale(${scale * hoverScale})
        rotate(${obj.rotation}deg)
      `,
      opacity,
      filter: `blur(${blur}px) ${isHovered ? 'brightness(1.15)' : ''}`,
      zIndex: Math.floor(10000 + effectiveZ),
      pointerEvents: (effectiveZ > -200 && effectiveZ < 400 ? 'auto' : 'none') as 'auto' | 'none',
      transition: 'filter 0.2s ease',
    }
  }

  if (transitionPhase === 'complete') {
    return null
  }

  return (
    <div 
      className="startpage-root app" 
      ref={containerRef} 
      style={{ 
        opacity: startPageOpacity,
        transition: 'opacity 0.3s ease-out',
      }}
    >
      <div className="scene-container">
        <header className="header">
          <div className="search-container">
            <button className="menu-btn">
              <Menu size={20} />
            </button>
            <div className="logo">chur-gpt</div>
            <button className="search-btn">
              <Search size={20} />
            </button>
          </div>
        </header>

        <div className={`objects-3d-container ${transitionPhase !== 'idle' ? 'transitioning' : ''}`}>
          {objects.map((obj) => (
            <div
              key={obj.id}
              className={`floating-object-3d ${hoveredObject === obj.id ? 'hovered' : ''}`}
              style={getObjectStyle(obj)}
              onMouseEnter={() => setHoveredObject(obj.id)}
              onMouseLeave={() => setHoveredObject(null)}
            >
              <img 
                src={obj.image} 
                alt="educational item" 
                style={{ 
                  width: '100%', 
                  height: '100%', 
                  objectFit: 'contain',
                }} 
              />
            </div>
          ))}
        </div>
      </div>

      {transitionPhase === 'idle' && (
        <div className="bottom-controls">
          <button 
            className="control-btn teacher-btn"
            onClick={teacherTransition}
          >
            <Layers size={18} />
            <span>Teacher</span>
          </button>
          <button 
            className="control-btn student-btn"
            onClick={studentTransition}
          >
            <Grid3X3 size={18} />
            <span>Student</span>
          </button>
        </div>
      )}

      <div 
        className="white-overlay"
        style={{ opacity: whiteOpacity }}
      />

      {transitionPhase === 'showName' && (
        <div 
          className="name-display"
          style={{ opacity: nameOpacity }}
        >
          <h1>chur-gpt</h1>
          <p>Student Learning Platform</p>
        </div>
      )}
    </div>
  )
}

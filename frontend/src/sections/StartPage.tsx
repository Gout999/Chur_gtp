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
  '/assets/books.png',
  '/assets/pencil.png',
  '/assets/graduation-cap.png',
  '/assets/apple.png',
  '/assets/globe.png',
  '/assets/calculator.png',
  '/assets/palette.png',
  '/assets/microscope.png',
  '/assets/trophy.png',
  '/assets/music-notes.png',
  '/assets/ruler.png',
  '/assets/scissors.png',
  '/assets/backpack.png',
  '/assets/lightbulb.png',
]

// Spawn distance (far away)
const SPAWN_Z = -3000
// Reset distance (when object passes camera)
const RESET_Z = 500
// Default auto-move speed
const DEFAULT_SPEED = 150

// Transition phases
 type TransitionPhase = 'idle' | 'zooming' | 'whiteout' | 'showName' | 'circleExpand' | 'complete'

interface StartPageProps {
  onPageChange: (page: PageType) => void;
}

export default function StartPage({ onPageChange }: StartPageProps) {
  const [objects, setObjects] = useState<FloatingObject[]>([])
  const [isGridView, setIsGridView] = useState(false)
  const [hoveredObject, setHoveredObject] = useState<number | null>(null)
  const [transitionPhase, setTransitionPhase] = useState<TransitionPhase>('idle')
  const [cameraZ, setCameraZ] = useState(0)
  const [whiteOpacity, setWhiteOpacity] = useState(0)
  const [circleScale, setCircleScale] = useState(0)
  const [nameOpacity, setNameOpacity] = useState(0)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const targetSpeedRef = useRef(1)
  const currentSpeedRef = useRef(1)
  const transitionStartTime = useRef<number | null>(null)

  // Initialize floating objects
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
        size: 100 + Math.random() * 80,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 0.2,
        speed: DEFAULT_SPEED + Math.random() * 50,
      }
    })
    setObjects(initialObjects)
  }, [])

  // Handle wheel event for speed control
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

  // Add wheel event listener
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('wheel', handleWheel, { passive: false })
    
    return () => {
      container.removeEventListener('wheel', handleWheel)
    }
  }, [handleWheel])

  // Start transition to student page
  const startTransition = useCallback(() => {
    if (transitionPhase !== 'idle') return
    setTransitionPhase('zooming')
    transitionStartTime.current = performance.now()
  }, [transitionPhase])

  // Animation loop
  useEffect(() => {
    let lastTime = performance.now()
    
    const animate = (time: number) => {
      const deltaTime = (time - lastTime) / 1000
      lastTime = time
      
      // Handle transition phases
      if (transitionPhase === 'zooming') {
        const elapsed = time - (transitionStartTime.current || time)
        const progress = Math.min(elapsed / 1900, 1) // 1.9 seconds zoom (reduced 0.1s)
        
        // Move camera forward (negative Z means moving into the scene)
        const targetCameraZ = -2500
        const newCameraZ = targetCameraZ * easeInOutCubic(progress)
        setCameraZ(newCameraZ)
        
        // Slow down speed during zoom
        targetSpeedRef.current = 0.2
        
        if (progress >= 1) {
          setTransitionPhase('whiteout')
          transitionStartTime.current = time
        }
      } else if (transitionPhase === 'whiteout') {
        const elapsed = time - (transitionStartTime.current || time)
        const progress = Math.min(elapsed / 800, 1)
        
        setWhiteOpacity(progress)
        
        if (progress >= 1) {
          setTransitionPhase('showName')
          transitionStartTime.current = time
        }
      } else if (transitionPhase === 'showName') {
        const elapsed = time - (transitionStartTime.current || time)
        
        if (elapsed < 300) {
          setNameOpacity(elapsed / 300)
        } else if (elapsed > 1000) {
          setNameOpacity(Math.max(0, 1 - (elapsed - 1000) / 300))
        } else {
          setNameOpacity(1)
        }
        
        if (elapsed > 1300) {
          setTransitionPhase('circleExpand')
          transitionStartTime.current = time
        }
      } else if (transitionPhase === 'circleExpand') {
        const elapsed = time - (transitionStartTime.current || time)
        const progress = Math.min(elapsed / 2200, 1) // 2.2 seconds circle expand (slower)
        
        setCircleScale(easeOutCubic(progress) * 150)
        
        if (progress >= 1) {
          setTransitionPhase('complete')
          setTimeout(() => {
            onPageChange('dashboard')
          }, 100)
        }
      }
      
      // Normal object animation
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
  }, [transitionPhase])

  // Easing functions
  const easeInOutCubic = (t: number) => {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
  }
  
  const easeOutCubic = (t: number) => {
    return 1 - Math.pow(1 - t, 3)
  }

  // Calculate 3D transform for each object
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

  return (
    <div className="startpage-root app" ref={containerRef} style={transitionPhase === 'circleExpand' || transitionPhase === 'complete' ? { 
    maskImage: `radial-gradient(circle at center, transparent 0%, transparent ${circleScale}vmax, black ${circleScale + 0.1}vmax, black 100%)`,
    WebkitMaskImage: `radial-gradient(circle at center, transparent 0%, transparent ${circleScale}vmax, black ${circleScale + 0.1}vmax, black 100%)`
  } : {}}>
      {/* 3D Scene Container */}
      <div className="scene-container">
        {/* Header */}
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

        {/* 3D Objects */}
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

      {/* Bottom Controls */}
      {transitionPhase === 'idle' && (
        <div className="bottom-controls">
          <button 
            className={`control-btn ${!isGridView ? 'active' : ''}`}
            onClick={() => setIsGridView(false)}
          >
            <Layers size={16} />
            <span>老師</span>
          </button>
          <button 
            className={`control-btn ${isGridView ? 'active' : ''}`}
            onClick={startTransition}
          >
            <Grid3X3 size={16} />
            <span>學生</span>
          </button>
        </div>
      )}

      {/* White Overlay */}
      <div 
        className="white-overlay"
        style={{ opacity: whiteOpacity }}
      />

      {/* Name Display */}
      {transitionPhase === 'showName' && (
        <div 
          className="name-display"
          style={{ opacity: nameOpacity }}
        >
          <h1>chur-gpt</h1>
          <p>學生學習平台</p>
        </div>
      )}


    </div>
  )
}



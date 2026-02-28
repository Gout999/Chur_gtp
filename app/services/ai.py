"""AI service for chat and material enhancement."""
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Try to import OpenAI, fall back to mock if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available. Using mock responses.")


# Initialize OpenAI client
openai_client = None
if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_chat_response(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Get AI chat response.
    
    Args:
        message: User message
        context: Optional context (previous messages, session info, etc.)
    
    Returns:
        AI response text
    """
    # If OpenAI is available, use it
    if openai_client:
        try:
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system",
                "content": """You are an AI tutor for ChurGPT, an intelligent learning platform. 
                Help students with their homework, explain concepts clearly, and provide guidance.
                Be encouraging and supportive while maintaining educational accuracy."""
            })
            
            # Add context if provided
            if context and "previous_messages" in context:
                messages.extend(context["previous_messages"])
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fall through to mock response
    
    # Mock response for development/testing
    return generate_mock_chat_response(message, context)


def generate_mock_chat_response(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Generate a mock chat response for development/testing."""
    import random
    
    # Simple keyword-based responses for testing
    if any(word in message.lower() for word in ["hello", "hi", "hey"]):
        return "Hello! I'm your AI tutor. How can I help you with your studies today?"
    
    if any(word in message.lower() for word in ["math", "mathematics", "calculate", "equation"]):
        return "I'd be happy to help with math! Please share the specific problem or concept you're working on, and I'll guide you through it step by step."
    
    if any(word in message.lower() for word in ["science", "physics", "chemistry", "biology"]):
        return "Science is fascinating! What topic would you like to explore? I can help explain concepts, work through problems, or clarify any confusion."
    
    if any(word in message.lower() for word in ["essay", "writing", "paper", "composition"]):
        return "I can help with writing! Whether you need help with structure, grammar, or developing your ideas, I'm here to assist. What are you working on?"
    
    if any(word in message.lower() for word in ["history", "historical", "past", "ancient"]):
        return "History helps us understand the present! What historical period or event are you studying?"
    
    if any(word in message.lower() for word in ["thank", "thanks", "appreciate"]):
        return "You're very welcome! I'm glad I could help. Feel free to ask if you have any other questions."
    
    # Generic helpful responses
    generic_responses = [
        "That's an interesting question! Let me think about it...",
        "I'd be happy to help with that. Could you provide more details about what you're looking for?",
        "Great question! Here's what I can tell you about that topic...",
        "I can definitely help with this. Let's break it down together.",
        "This is a good learning opportunity! Let me explain..."
    ]
    
    return random.choice(generic_responses)


def process_enhancement(enhancement_id: int):
    """Process material enhancement in background.
    
    Args:
        enhancement_id: ID of the EnhancedNote to process
    """
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import EnhancedNote, Material
    
    # Create a new DB session for background task
    db = SessionLocal()
    
    try:
        # Get enhancement record
        enhancement = db.query(EnhancedNote).filter(
            EnhancedNote.id == enhancement_id
        ).first()
        
        if not enhancement:
            logger.error(f"Enhancement {enhancement_id} not found")
            return
        
        # Update status to processing
        enhancement.status = "processing"
        db.commit()
        
        # Get material
        material = db.query(Material).filter(
            Material.id == enhancement.material_id
        ).first()
        
        if not material:
            enhancement.status = "failed"
            enhancement.error_message = "Material not found"
            db.commit()
            return
        
        # Get enhancement settings
        settings = enhancement.enhancement_settings or {}
        study_mode = settings.get("study_mode", "detailed")
        focus = settings.get("focus", "all")
        style = settings.get("style", "bullet_points")
        
        # Generate enhanced content
        if openai_client:
            try:
                enhanced_content = generate_enhancement_with_openai(
                    material.title,
                    material.description or "",
                    study_mode,
                    focus,
                    style
                )
            except Exception as e:
                logger.error(f"OpenAI enhancement error: {e}")
                enhanced_content = generate_mock_enhancement(
                    material.title,
                    study_mode,
                    focus,
                    style
                )
        else:
            enhanced_content = generate_mock_enhancement(
                material.title,
                study_mode,
                focus,
                style
            )
        
        # Save result
        enhancement.content = enhanced_content
        enhancement.status = "completed"
        db.commit()
        
        logger.info(f"Enhancement {enhancement_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing enhancement {enhancement_id}: {e}")
        
        # Update status to failed
        enhancement = db.query(EnhancedNote).filter(
            EnhancedNote.id == enhancement_id
        ).first()
        
        if enhancement:
            enhancement.status = "failed"
            enhancement.error_message = str(e)
            db.commit()
    
    finally:
        db.close()


def generate_enhancement_with_openai(
    title: str,
    description: str,
    study_mode: str,
    focus: str,
    style: str
) -> str:
    """Generate enhanced content using OpenAI API."""
    
    # Build prompt based on settings
    prompt = f"""Please create enhanced study notes for the following material:

Title: {title}
Description: {description}

Requirements:
- Study Mode: {study_mode} (quick summary vs detailed explanation vs exam prep)
- Focus: {focus} (concepts, examples, practice problems, or all)
- Style: {style} (bullet points, paragraphs, tables, or mind map format)

Please provide comprehensive, well-structured notes that will help a student understand and remember this material effectively."""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert educator creating study materials."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.7
    )
    
    return response.choices[0].message.content


def generate_mock_enhancement(
    title: str,
    study_mode: str,
    focus: str,
    style: str
) -> str:
    """Generate mock enhanced content for testing."""
    
    study_mode_desc = {
        "quick": "Quick Summary",
        "detailed": "Detailed Study Notes",
        "exam_prep": "Exam Preparation Guide"
    }
    
    focus_desc = {
        "concepts": "Key Concepts",
        "examples": "Worked Examples",
        "practice": "Practice Problems",
        "all": "Complete Coverage"
    }
    
    mode_text = study_mode_desc.get(study_mode, "Study Notes")
    focus_text = focus_desc.get(focus, "All Topics")
    
    content = f"""# {mode_text}: {title}

## {focus_text}

This is an AI-enhanced version of the study material "{title}".

### Key Points

1. **Main Concept**: The fundamental principles and core ideas
2. **Important Details**: Critical information to remember
3. **Practical Applications**: How to apply this knowledge
4. **Common Mistakes**: Pitfalls to avoid

### Summary

This enhanced material provides {study_mode} level coverage with focus on {focus}. 
The notes are formatted in {style} style for optimal learning.

---
*Generated by ChurGPT AI Enhancement*
*Study Mode: {study_mode} | Focus: {focus} | Style: {style}*
"""
    
    return content

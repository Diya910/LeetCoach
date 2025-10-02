"""
Screen analysis router for LeetCoach application.
Handles screen capture analysis and assistance detection.
"""

import base64
import io
import json
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from PIL import Image
import cv2
import numpy as np

from ..config import settings
from ..orchestrator import DynamicAgentOrchestrator

router = APIRouter(prefix="/api/screen", tags=["screen"])

# Initialize orchestrator
orchestrator = DynamicAgentOrchestrator()


@router.post("/analyze")
async def analyze_screen(
    image_data: str = Form(...),
    url: str = Form(...),
    timestamp: int = Form(...)
) -> Dict[str, Any]:
    """
    Analyze screen capture to detect LeetCode problems and user state.
    
    Args:
        image_data: Base64 encoded image data
        url: Current page URL
        timestamp: Timestamp of capture
        
    Returns:
        Analysis results including problem detection and assistance needs
    """
    try:
        # Decode image data
        image_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Check file size and compress if needed (limit to 400KB to avoid 1024KB limit)
        if len(image_bytes) > 400 * 1024:  # 400KB limit
            print(f"Image too large ({len(image_bytes)} bytes), compressing...")
            # Compress image if too large
            image = Image.open(io.BytesIO(image_bytes))
            # Resize to reduce file size
            width, height = image.size
            if width > 1280 or height > 720:  # More aggressive resizing
                image.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            
            # Convert to JPEG with higher compression
            output = io.BytesIO()
            image = image.convert('RGB')
            image.save(output, format='JPEG', quality=50, optimize=True)  # Lower quality for smaller size
            image_bytes = output.getvalue()
            print(f"Compressed to {len(image_bytes)} bytes")
            
            # If still too large, compress more aggressively
            if len(image_bytes) > 400 * 1024:
                image = Image.open(io.BytesIO(image_bytes))
                image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=30, optimize=True)
                image_bytes = output.getvalue()
                print(f"Further compressed to {len(image_bytes)} bytes")
            
            image = Image.open(io.BytesIO(image_bytes))
        else:
            image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format for analysis
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Analyze the screen
        analysis = await analyze_screen_content(cv_image, url)
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screen analysis failed: {str(e)}")


@router.post("/assistance-need")
async def analyze_assistance_need(
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze if user needs assistance based on context.
    
    Args:
        context: User context including code, problem, behavior
        
    Returns:
        Assistance recommendation
    """
    try:
        # Use orchestrator to analyze assistance need
        response = await orchestrator.process_dynamic_request(
            user_request="Analyze if the user needs assistance based on their current state",
            context_data=context
        )
        
        # Extract assistance recommendation
        needs_assistance = analyze_assistance_indicators(context, response.response)
        
        return {
            "success": True,
            "needs_assistance": needs_assistance,
            "reasoning": response.response,
            "confidence": response.confidence_score
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistance analysis failed: {str(e)}")


async def analyze_screen_content(cv_image: np.ndarray, url: str) -> Dict[str, Any]:
    """
    Analyze screen content to detect LeetCode problems and user state.
    
    Args:
        cv_image: OpenCV image array
        url: Current page URL
        
    Returns:
        Analysis results
    """
    analysis = {
        "is_leetcode_problem": False,
        "problem_detected": None,
        "user_state": "unknown",
        "needs_assistance": False,
        "confidence": 0.0
    }
    
    try:
        # Check URL patterns
        if "leetcode.com/problems" in url:
            analysis["is_leetcode_problem"] = True
            analysis["confidence"] += 0.3
        
        # Use OCR to detect text patterns
        text_content = extract_text_from_image(cv_image)
        
        # Look for LeetCode-specific patterns
        leetcode_patterns = [
            "leetcode", "problem", "solution", "submit", "run code",
            "test cases", "constraints", "example", "difficulty"
        ]
        
        pattern_matches = sum(1 for pattern in leetcode_patterns 
                            if pattern.lower() in text_content.lower())
        
        if pattern_matches >= 3:
            analysis["is_leetcode_problem"] = True
            analysis["confidence"] += 0.4
        
        # Detect problem title
        problem_title = extract_problem_title(text_content)
        if problem_title:
            analysis["problem_detected"] = {
                "title": problem_title,
                "confidence": 0.8
            }
            analysis["confidence"] += 0.3
        
        # Analyze user state
        user_state = analyze_user_state(cv_image, text_content)
        analysis["user_state"] = user_state
        
        # Determine if assistance is needed
        analysis["needs_assistance"] = determine_assistance_need(
            analysis["is_leetcode_problem"],
            user_state,
            analysis["confidence"]
        )
        
    except Exception as e:
        print(f"Screen analysis error: {e}")
        analysis["error"] = str(e)
    
    return analysis


def extract_text_from_image(cv_image: np.ndarray) -> str:
    """
    Extract text from image using OCR.
    
    Args:
        cv_image: OpenCV image array
        
    Returns:
        Extracted text
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Use pytesseract for OCR (if available)
        try:
            import pytesseract
            # Set tesseract path if needed (Windows)
            import platform
            if platform.system() == "Windows":
                # Try common tesseract paths on Windows
                tesseract_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
                ]
                for path in tesseract_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
            
            text = pytesseract.image_to_string(thresh)
            return text
        except (ImportError, Exception) as e:
            # Fallback: return basic text detection
            print(f"Text extraction error: {e}")
            return "Text extraction not available"
            
    except Exception as e:
        print(f"Text extraction error: {e}")
        return ""


def extract_problem_title(text: str) -> Optional[str]:
    """
    Extract problem title from text content.
    
    Args:
        text: Extracted text content
        
    Returns:
        Problem title if found
    """
    try:
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for patterns that might be problem titles
            if (len(line) > 5 and len(line) < 100 and 
                not line.lower().startswith(('input:', 'output:', 'example', 'constraints'))):
                # Check if it looks like a problem title
                if any(word in line.lower() for word in ['sum', 'array', 'tree', 'list', 'string', 'number']):
                    return line
        return None
    except Exception:
        return None


def analyze_user_state(cv_image: np.ndarray, text: str) -> str:
    """
    Analyze user's current state based on screen content.
    
    Args:
        cv_image: OpenCV image array
        text: Extracted text content
        
    Returns:
        User state description
    """
    try:
        # Look for code editor indicators
        if any(word in text.lower() for word in ['def ', 'function', 'class ', 'import ', 'return']):
            return "coding"
        
        # Look for error indicators
        if any(word in text.lower() for word in ['error', 'exception', 'failed', 'wrong answer']):
            return "debugging"
        
        # Look for empty or minimal content
        if len(text.strip()) < 100:
            return "starting"
        
        # Look for submission indicators
        if any(word in text.lower() for word in ['submit', 'accepted', 'runtime', 'memory']):
            return "submitting"
        
        return "reading"
        
    except Exception:
        return "unknown"


def determine_assistance_need(
    is_leetcode: bool, 
    user_state: str, 
    confidence: float
) -> bool:
    """
    Determine if user needs assistance based on analysis.
    
    Args:
        is_leetcode: Whether this is a LeetCode problem page
        user_state: Current user state
        confidence: Analysis confidence
        
    Returns:
        Whether assistance is needed
    """
    if not is_leetcode or confidence < 0.5:
        return False
    
    # States that typically need assistance
    assistance_states = ["debugging", "starting"]
    
    return user_state in assistance_states


def analyze_assistance_indicators(context: Dict[str, Any], ai_response: str) -> bool:
    """
    Analyze assistance indicators from context and AI response.
    
    Args:
        context: User context
        ai_response: AI analysis response
        
    Returns:
        Whether assistance is needed
    """
    try:
        # Check context indicators
        user_code = context.get('userCode', {})
        if user_code and not user_code.get('isWorking', True):
            return True
        
        # Check time on page
        time_on_page = context.get('timeOnPage', 0)
        if time_on_page > 300:  # 5 minutes
            return True
        
        # Check stuck metrics
        stuck_metrics = context.get('stuckMetrics', {})
        if any(value > 2 for value in stuck_metrics.values()):
            return True
        
        # Check AI response for assistance indicators
        assistance_keywords = [
            'stuck', 'help', 'assistance', 'guidance', 'hint',
            'error', 'problem', 'issue', 'difficulty'
        ]
        
        if any(keyword in ai_response.lower() for keyword in assistance_keywords):
            return True
        
        return False
        
    except Exception:
        return False

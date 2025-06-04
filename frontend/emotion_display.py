#!/usr/bin/env python3
"""
Week 2 Completion: Simple Emotion Display UI for SentioAI
A Streamlit web interface to display real-time emotion detection
"""

import streamlit as st
import cv2
import numpy as np
import time
import threading
from datetime import datetime
import sys
import os

# Add the models directory to path so we can import our emotion detector
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models', 'emotion_detection'))

try:
    from emotion_classifier import EmotionDetector
except ImportError:
    st.error("Could not import EmotionDetector. Make sure you're running from the project root directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="SentioAI - Emotion Detection",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for emotion-based styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #4A90E2;
        margin-bottom: 2rem;
    }
    
    .emotion-display {
        text-align: center;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .emotion-happy { background: linear-gradient(135deg, #FFE066, #FFF566); color: #B8860B; }
    .emotion-sad { background: linear-gradient(135deg, #4A90E2, #7BB3F0); color: white; }
    .emotion-angry { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: white; }
    .emotion-surprise { background: linear-gradient(135deg, #FFD93D, #FFED4A); color: #B8860B; }
    .emotion-fear { background: linear-gradient(135deg, #9B59B6, #BB77C4); color: white; }
    .emotion-disgust { background: linear-gradient(135deg, #2ECC71, #58D68D); color: white; }
    .emotion-neutral { background: linear-gradient(135deg, #BDC3C7, #D5DBDB); color: #34495E; }
    
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .timeline-item {
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-left: 4px solid #4A90E2;
        background: #F8F9FA;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'detector' not in st.session_state:
    st.session_state.detector = None
if 'camera_running' not in st.session_state:
    st.session_state.camera_running = False
if 'current_emotion' not in st.session_state:
    st.session_state.current_emotion = {'emotion': 'neutral', 'confidence': 0.0}
if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = None

def get_emotion_emoji(emotion):
    """Get emoji for emotion"""
    emoji_map = {
        'happy': '😊',
        'sad': '😔',
        'angry': '😠',
        'surprise': '😲',
        'fear': '😨',
        'disgust': '🤢',
        'neutral': '😐'
    }
    return emoji_map.get(emotion, '😐')

def get_emotion_color(emotion):
    """Get background color class for emotion"""
    return f"emotion-{emotion}"

def start_emotion_detection():
    """Start the emotion detection process"""
    try:
        st.session_state.detector = EmotionDetector(smoothing_window=8, detection_interval=2.0)
        st.session_state.camera_running = True
        st.session_state.session_start_time = datetime.now()
        return True
    except Exception as e:
        st.error(f"Failed to start emotion detection: {e}")
        return False

def stop_emotion_detection():
    """Stop the emotion detection process"""
    st.session_state.camera_running = False
    if st.session_state.detector:
        st.session_state.detector = None

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 SentioAI - Real-Time Emotion Detection</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Week 2 MVP: Testing Facial Emotion Recognition</p>', unsafe_allow_html=True)
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if not st.session_state.camera_running:
            if st.button("🎥 Start Emotion Detection", use_container_width=True):
                if start_emotion_detection():
                    st.rerun()
        else:
            if st.button("⏹️ Stop Detection", use_container_width=True):
                stop_emotion_detection()
                st.rerun()
    
    # Main interface
    if st.session_state.camera_running and st.session_state.detector:
        # Create two columns: camera feed simulation and emotion display
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📹 Camera Feed")
            
            # Placeholder for camera feed (Streamlit doesn't support real-time webcam display easily)
            camera_placeholder = st.empty()
            camera_placeholder.info("🎥 Camera is running in background\n\n💡 Look at your webcam to detect emotions!\n\n⚠️ Note: Live camera feed not shown in web interface (this is normal)")
            
            # Camera status
            if st.session_state.session_start_time:
                duration = datetime.now() - st.session_state.session_start_time
                st.metric("Session Duration", f"{duration.seconds // 60}m {duration.seconds % 60}s")
        
        with col2:
            st.subheader("🧠 Emotion Analysis")
            
            # Current emotion display
            current_emotion = st.session_state.current_emotion
            emotion = current_emotion['emotion']
            confidence = current_emotion['confidence']
            emoji = get_emotion_emoji(emotion)
            
            # Emotion display box
            emotion_html = f"""
            <div class="emotion-display {get_emotion_color(emotion)}">
                {emoji} {emotion.upper()}
                <br>
                <small style="font-size: 1rem;">Confidence: {confidence:.1f}%</small>
            </div>
            """
            st.markdown(emotion_html, unsafe_allow_html=True)
            
            # Metrics
            col_metrics1, col_metrics2 = st.columns(2)
            with col_metrics1:
                st.metric("Current Emotion", emotion.title())
            with col_metrics2:
                st.metric("Confidence", f"{confidence:.1f}%")
        
        # Emotion Timeline
        st.subheader("📊 Emotion Timeline")
        
        if st.session_state.detector and st.session_state.detector.get_emotion_log():
            emotion_log = st.session_state.detector.get_emotion_log()
            
            # Display recent emotions
            st.write("**Recent Emotion Log:**")
            for entry in emotion_log[-5:]:  # Show last 5 entries
                emoji = get_emotion_emoji(entry['emotion'])
                st.markdown(f"""
                <div class="timeline-item">
                    {emoji} <strong>{entry['emotion'].title()}</strong> at {entry['readable_time']}
                </div>
                """, unsafe_allow_html=True)
            
            # Session summary
            if len(emotion_log) > 0:
                summary = st.session_state.detector.get_session_summary()
                if isinstance(summary, dict):
                    st.subheader("📈 Session Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Duration", f"{summary['duration_minutes']} min")
                    with col2:
                        st.metric("Emotions Logged", summary['total_emotions_logged'])
                    with col3:
                        st.metric("Most Common", summary['most_common_emotion'].title())
                    
                    # Emotion breakdown
                    if summary['emotion_breakdown']:
                        st.write("**Emotion Breakdown:**")
                        for emotion, count in summary['emotion_breakdown'].items():
                            percentage = (count / summary['total_emotions_logged']) * 100
                            st.write(f"{get_emotion_emoji(emotion)} {emotion.title()}: {count} times ({percentage:.1f}%)")
        else:
            st.info("🕐 Emotion logging will appear here... (emotions are logged every 15 seconds)")
        
        # Auto-refresh for real-time updates
        time.sleep(2)
        st.rerun()
    
    else:
        # Welcome screen
        st.info("""
        👋 **Welcome to SentioAI Emotion Detection!**
        
        This is the Week 2 MVP interface. Click "Start Emotion Detection" to begin.
        
        **What this does:**
        - 🎥 Uses your webcam to detect facial emotions
        - 🧠 Identifies 7 emotions: happy, sad, angry, surprise, fear, disgust, neutral
        - 📊 Logs emotions every 15 seconds for timeline tracking
        - ✨ Shows real-time emotion analysis with confidence scores
        
        **Note:** The actual camera feed runs in the background. The web interface shows the detected emotions and analysis.
        """)
        
        # Instructions
        with st.expander("📋 Instructions"):
            st.write("""
            1. **Click "Start Emotion Detection"** to begin
            2. **Look at your webcam** - the system will detect your facial expressions
            3. **Try different expressions** to see how accurately it detects emotions
            4. **Check the timeline** to see your emotion history
            5. **Click "Stop Detection"** when finished
            
            **Tips:**
            - Make sure your face is well-lit and visible to the camera
            - Try exaggerated expressions for better detection
            - The system smooths emotions over time for accuracy
            """)

if __name__ == "__main__":
    main()
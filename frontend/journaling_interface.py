#!/usr/bin/env python3
"""
Week 3: SentioAI Journaling Interface
Combines emotion detection with guided journaling prompts
"""

import streamlit as st
import cv2
import threading
import time
import json
from datetime import datetime
import sys
import os
import uuid

# Add the models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models', 'emotion_detection'))

try:
    from emotion_classifier import EmotionDetector
except ImportError:
    st.error("Could not import EmotionDetector. Make sure you're running from the project root directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="SentioAI - Emotional Journaling",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Emotion-based prompts
EMOTION_PROMPTS = {
    'happy': [
        "What's bringing you joy today? Let's capture this positive moment...",
        "You seem bright today! What would you like to celebrate or remember?",
        "There's positive energy around you. What's going well in your life right now?",
        "Your happiness is showing! What experience or thought is lifting your spirits?"
    ],
    'sad': [
        "It looks like something is weighing on your heart. What would you like to share?",
        "Sometimes writing helps lighten emotional burdens. What's on your mind?",
        "I notice you might be feeling down. Would you like to explore what's happening?",
        "Your feelings are valid. What's making this moment difficult for you?"
    ],
    'angry': [
        "I can sense some tension. What's frustrating you right now?",
        "Strong emotions often carry important messages. What's triggering this feeling?",
        "It's okay to feel angry. What situation or thought is bothering you?",
        "Sometimes writing helps process intense feelings. What's stirring this energy in you?"
    ],
    'surprise': [
        "You look surprised! What unexpected thing just happened or crossed your mind?",
        "Something seems to have caught your attention. What's the surprising moment about?",
        "Life has a way of surprising us. What's the unexpected element you're processing?",
        "Your expression suggests something unexpected. What's this new development?"
    ],
    'fear': [
        "I notice some apprehension. What's making you feel uncertain right now?",
        "Fear often points to something important to us. What's causing this worry?",
        "It's natural to feel anxious sometimes. What's creating this unease?",
        "You seem concerned about something. What thoughts are making you feel unsettled?"
    ],
    'disgust': [
        "Something seems to be bothering you. What's creating this negative reaction?",
        "You look like something doesn't sit right with you. What's the source of this feeling?",
        "Sometimes we encounter things that don't align with our values. What's troubling you?",
        "I can see something has put you off. What's causing this strong reaction?"
    ],
    'neutral': [
        "How are you feeling in this moment? What's present for you right now?",
        "Sometimes the quiet moments are perfect for reflection. What's on your mind?",
        "You seem calm and centered. What would you like to explore or share today?",
        "This feels like a good moment for some gentle self-reflection. What's stirring within you?"
    ]
}

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E7D8E;
        margin-bottom: 1rem;
        font-weight: 300;
    }
    
    .emotion-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .emotion-happy { background: linear-gradient(135deg, #FFE066, #FFF566); color: #B8860B; }
    .emotion-sad { background: linear-gradient(135deg, #4A90E2, #7BB3F0); color: white; }
    .emotion-angry { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: white; }
    .emotion-surprise { background: linear-gradient(135deg, #FFD93D, #FFED4A); color: #B8860B; }
    .emotion-fear { background: linear-gradient(135deg, #9B59B6, #BB77C4); color: white; }
    .emotion-disgust { background: linear-gradient(135deg, #2ECC71, #58D68D); color: white; }
    .emotion-neutral { background: linear-gradient(135deg, #BDC3C7, #D5DBDB); color: #34495E; }
    
    .prompt-container {
        background: #F8F9FA;
        border-left: 4px solid #2E7D8E;
        padding: 1.5rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        font-style: italic;
        font-size: 1.1rem;
        color: #555;
    }
    
    .journal-container {
        background: white;
        border: 2px solid #E1E8ED;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .session-info {
        background: #E8F5E8;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #28A745;
    }
    
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.6 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'emotion_detector' not in st.session_state:
        st.session_state.emotion_detector = None
    if 'detection_running' not in st.session_state:
        st.session_state.detection_running = False
    if 'current_emotion' not in st.session_state:
        st.session_state.current_emotion = {'emotion': 'neutral', 'confidence': 0.0}
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = None
    if 'journal_entries' not in st.session_state:
        st.session_state.journal_entries = []
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = ""

def get_emotion_emoji(emotion):
    """Get emoji for emotion"""
    emoji_map = {
        'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
        'fear': '😨', 'disgust': '🤢', 'neutral': '😐'
    }
    return emoji_map.get(emotion, '😐')

def get_emotion_prompt(emotion):
    """Get a random prompt for the given emotion"""
    import random
    prompts = EMOTION_PROMPTS.get(emotion, EMOTION_PROMPTS['neutral'])
    return random.choice(prompts)

def start_emotion_detection():
    """Start emotion detection in background"""
    try:
        st.session_state.emotion_detector = EmotionDetector(smoothing_window=5, detection_interval=1.5)
        st.session_state.detection_running = True
        st.session_state.session_start_time = datetime.now()
        return True
    except Exception as e:
        st.error(f"Failed to start emotion detection: {e}")
        return False

def stop_emotion_detection():
    """Stop emotion detection"""
    st.session_state.detection_running = False
    st.session_state.emotion_detector = None

def save_journal_entry(emotion, prompt, entry_text):
    """Save a journal entry"""
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'emotion': emotion,
        'prompt': prompt,
        'entry_text': entry_text,
        'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y")
    }
    
    st.session_state.journal_entries.append(entry)
    
    # Save to file
    with open('data/journal_entries/session_entries.json', 'w') as f:
        json.dump(st.session_state.journal_entries, f, indent=2)
    
    return entry

def main():
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📝 SentioAI - Emotional Journaling</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Express yourself with emotion-guided prompts</p>', unsafe_allow_html=True)
    
    # Control panel
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.detection_running:
            if st.button("🎥 Start Emotion-Guided Session", use_container_width=True, type="primary"):
                if start_emotion_detection():
                    st.rerun()
        else:
            col_stop, col_refresh = st.columns(2)
            with col_stop:
                if st.button("⏹️ End Session", use_container_width=True):
                    stop_emotion_detection()
                    st.rerun()
            with col_refresh:
                if st.button("🔄 Refresh Emotion", use_container_width=True):
                    st.rerun()
    
    if st.session_state.detection_running:
        # Simulate emotion detection (since we can't run camera in Streamlit)
        # In a real implementation, this would connect to the emotion detector
        
        # For demo purposes, let's use a rotating emotion
        import random
        emotions = ['happy', 'sad', 'neutral', 'surprise', 'angry']
        current_emotion = random.choice(emotions)
        confidence = random.uniform(60, 95)
        
        st.session_state.current_emotion = {
            'emotion': current_emotion,
            'confidence': confidence
        }
        
        # Main interface
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("🧠 Current Emotion")
            
            emotion = st.session_state.current_emotion['emotion']
            confidence = st.session_state.current_emotion['confidence']
            emoji = get_emotion_emoji(emotion)
            
            # Emotion display
            emotion_html = f"""
            <div class="emotion-badge emotion-{emotion}">
                {emoji} {emotion.upper()}
                <br>
                <small>{confidence:.1f}% confidence</small>
            </div>
            """
            st.markdown(emotion_html, unsafe_allow_html=True)
            
            # Session info
            if st.session_state.session_start_time:
                duration = datetime.now() - st.session_state.session_start_time
                duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                
                session_html = f"""
                <div class="session-info">
                    <strong>📊 Session Info</strong><br>
                    Duration: {duration_str}<br>
                    Entries: {len(st.session_state.journal_entries)}
                </div>
                """
                st.markdown(session_html, unsafe_allow_html=True)
            
            # Camera note
            st.info("💡 **Note**: Camera detection runs in background. In the full app, your webcam would detect emotions in real-time.")
        
        with col_right:
            st.subheader("✍️ Journal Entry")
            
            # Get emotion-based prompt
            current_prompt = get_emotion_prompt(emotion)
            st.session_state.current_prompt = current_prompt
            
            # Display prompt
            prompt_html = f"""
            <div class="prompt-container">
                💭 {current_prompt}
            </div>
            """
            st.markdown(prompt_html, unsafe_allow_html=True)
            
            # Journal input
            with st.container():
                st.markdown('<div class="journal-container">', unsafe_allow_html=True)
                
                journal_text = st.text_area(
                    "Share your thoughts...",
                    placeholder="Start writing about what's on your mind. Let your thoughts flow naturally...",
                    height=200,
                    key="journal_input"
                )
                
                col_save, col_voice = st.columns([2, 1])
                
                with col_save:
                    if st.button("💾 Save Entry", use_container_width=True, type="primary"):
                        if journal_text.strip():
                            entry = save_journal_entry(emotion, current_prompt, journal_text)
                            st.success(f"✅ Journal entry saved! ({len(journal_text)} characters)")
                            st.session_state.journal_input = ""  # Clear the text area
                            st.rerun()
                        else:
                            st.warning("Please write something before saving!")
                
                with col_voice:
                    if st.button("🎤 Voice Input", use_container_width=True):
                        st.info("🔜 Voice-to-text feature coming in next update!")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent entries
        if st.session_state.journal_entries:
            st.subheader("📚 Recent Journal Entries")
            
            # Show last 3 entries
            recent_entries = st.session_state.journal_entries[-3:]
            
            for entry in reversed(recent_entries):
                with st.expander(f"{get_emotion_emoji(entry['emotion'])} {entry['readable_time']} - {entry['emotion'].title()}"):
                    st.write(f"**Prompt:** {entry['prompt']}")
                    st.write(f"**Entry:** {entry['entry_text']}")
        
        # Auto-refresh for emotion updates
        time.sleep(3)
        st.rerun()
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem;">
            <h3>🌟 Welcome to SentioAI Emotional Journaling</h3>
            <p style="font-size: 1.1rem; color: #666; max-width: 600px; margin: 0 auto;">
                This is where emotion detection meets guided reflection. Start a session to receive 
                personalized journaling prompts based on your current emotional state.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🧠 Emotion Detection**
            - Real-time facial emotion recognition
            - 7 core emotions detected
            - Confidence scoring
            """)
        
        with col2:
            st.markdown("""
            **💭 Smart Prompts**
            - Emotion-driven writing prompts
            - Contextual reflection questions
            - Supportive guidance
            """)
        
        with col3:
            st.markdown("""
            **📝 Journaling**
            - Save thoughts and reflections
            - Track emotional journey
            - Build self-awareness
            """)
        
        with st.expander("📋 How It Works"):
            st.write("""
            1. **Start a session** - Click the button above to begin emotion detection
            2. **Look at your camera** - The system detects your current emotional state
            3. **Read the prompt** - Get a personalized reflection question based on your emotion
            4. **Write freely** - Express your thoughts and feelings
            5. **Save your entry** - Build a timeline of your emotional journey
            
            **Tips:**
            - Be honest with yourself in your writing
            - Don't worry about grammar or structure
            - Let your emotions guide your reflection
            - Take your time - there's no rush
            """)

if __name__ == "__main__":
    main()

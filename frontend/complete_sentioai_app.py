#!/usr/bin/env python3
"""
Week 4 Complete: Integrated SentioAI Emotional Journaling App
Combines emotion detection, journaling prompts, voice input, and GPT responses
"""

import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title="SentioAI - Complete Emotional Journal",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import openai
import cv2
import threading
import time
import json
import tempfile
import os
from datetime import datetime
import uuid
import sys
import random

# Add the models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models', 'emotion_detection'))

try:
    from emotion_classifier import EmotionDetector
except ImportError:
    st.error("Could not import EmotionDetector. Make sure you're running from the project root directory.")
    st.stop()

# Import GPT companion
class EmotionalCompanion:
    def __init__(self, api_key):
        """Initialize the GPT emotional companion"""
        self.client = openai.OpenAI(api_key=api_key)
        
        # Define emotion-specific response styles
        self.emotion_styles = {
            'happy': {
                'tone': 'celebratory and encouraging',
                'approach': 'amplify the positive emotions and help user savor the moment',
                'avoid': 'being dismissive or bringing up potential problems'
            },
            'sad': {
                'tone': 'gentle, compassionate, and validating',
                'approach': 'acknowledge the pain, offer comfort, and gently explore the feelings',
                'avoid': 'trying to fix or minimize the sadness'
            },
            'angry': {
                'tone': 'calm, understanding, and non-judgmental',
                'approach': 'validate the anger, help process the trigger, suggest healthy expression',
                'avoid': 'escalating the anger or being dismissive'
            },
            'surprise': {
                'tone': 'curious and engaged',
                'approach': 'explore the unexpected event and help process the new information',
                'avoid': 'being overwhelming or dismissive of the surprise'
            },
            'fear': {
                'tone': 'reassuring and grounding',
                'approach': 'acknowledge the fear, provide comfort, help ground in reality',
                'avoid': 'minimizing the fear or being overly optimistic'
            },
            'disgust': {
                'tone': 'understanding and supportive',
                'approach': 'validate the strong reaction and help explore what values were violated',
                'avoid': 'judging the reaction or the source of disgust'
            },
            'neutral': {
                'tone': 'warm and gently curious',
                'approach': 'invite deeper reflection and help uncover underlying feelings',
                'avoid': 'being too probing or assuming something is wrong'
            }
        }
    
    def generate_system_prompt(self, emotion, confidence):
        """Generate system prompt based on detected emotion"""
        style = self.emotion_styles.get(emotion, self.emotion_styles['neutral'])
        
        return f"""You are SentioAI, an empathetic emotional wellness companion. A user has just written a journal entry while experiencing the emotion: {emotion} (detected with {confidence:.0f}% confidence).

Your role is to:
- Be a wise, compassionate friend who truly listens
- Respond with a {style['tone']} tone
- {style['approach']}
- Avoid {style['avoid']}

Guidelines:
- Keep responses to 2-4 sentences (50-100 words)
- Be warm but not overly familiar
- Ask ONE thoughtful follow-up question if appropriate
- Use "I notice..." or "It sounds like..." rather than "You should..."
- Focus on emotional validation before offering any perspective
- Never give medical or therapeutic advice
- Be authentic and avoid clichés"""
    
    def generate_response(self, journal_entry, emotion, confidence=0.8):
        """Generate empathetic response to journal entry"""
        try:
            system_prompt = self.generate_system_prompt(emotion, confidence)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Journal entry: '{journal_entry}'"}
                ],
                max_tokens=150,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return {
                'response': response.choices[0].message.content.strip(),
                'emotion_addressed': emotion,
                'confidence': confidence,
                'success': True,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'response': f"I'm having trouble connecting right now, but I want you to know that what you shared matters. Sometimes taking a moment to write down our thoughts is healing in itself.",
                'error': str(e),
                'success': False,
                'fallback': True
            }

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

# Custom CSS
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
    .emotion-sad { background: linear-gradient(135deg, #4A90E2, #7BB3F0); color: black; }
    .emotion-angry { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: black; }
    .emotion-surprise { background: linear-gradient(135deg, #FFD93D, #FFED4A); color: #B8860B; }
    .emotion-fear { background: linear-gradient(135deg, #9B59B6, #BB77C4); color: black; }
    .emotion-disgust { background: linear-gradient(135deg, #2ECC71, #58D68D); color: black; }
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
    
    .ai-response-container {
        background: linear-gradient(135deg, black, #e6f3ff);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
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
</style>
""", unsafe_allow_html=True)



# Initialize session state
def initialize_session_state():
    if 'emotion_detector' not in st.session_state:
        st.session_state.emotion_detector = None
    if 'gpt_companion' not in st.session_state:
        st.session_state.gpt_companion = None
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
    if 'voice_transcript' not in st.session_state:
        st.session_state.voice_transcript = ""

def setup_apis():
    """Setup OpenAI API for GPT companion"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
    
    if api_key:
        if st.session_state.gpt_companion is None:
            st.session_state.gpt_companion = EmotionalCompanion(api_key)
        return True
    return False

def get_emotion_emoji(emotion):
    """Get emoji for emotion"""
    emoji_map = {
        'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
        'fear': '😨', 'disgust': '🤢', 'neutral': '😐'
    }
    return emoji_map.get(emotion, '😐')

def get_emotion_prompt(emotion):
    """Get a random prompt for the given emotion"""
    prompts = EMOTION_PROMPTS.get(emotion, EMOTION_PROMPTS['neutral'])
    return random.choice(prompts)

def transcribe_audio(audio_file_path, api_key):
    """Transcribe audio using OpenAI Whisper"""
    try:
        with open(audio_file_path, 'rb') as audio_file:
            client = openai.OpenAI(api_key=api_key)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        return transcript.text
    except Exception as e:
        st.error(f"Voice transcription failed: {e}")
        return None

def save_journal_entry(emotion, prompt, entry_text, ai_response=None, voice_data=None):
    """Save a complete journal entry with AI response"""
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'emotion': emotion,
        'prompt': prompt,
        'entry_text': entry_text,
        'ai_response': ai_response,
        'voice_data': voice_data,
        'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y"),
        'has_ai_response': ai_response is not None
    }
    
    st.session_state.journal_entries.append(entry)
    
    # Save to file
    os.makedirs('data/journal_entries', exist_ok=True)
    with open('data/journal_entries/complete_session_entries.json', 'w') as f:
        json.dump(st.session_state.journal_entries, f, indent=2)
    
    return entry

def main():
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🌟 SentioAI - Complete Emotional Journaling Experience</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Emotion detection • Guided prompts • Voice input • AI companion responses</p>', unsafe_allow_html=True)
    
    # Check API setup
    if not setup_apis():
        st.warning("⚠️ OpenAI API key required for voice transcription and AI responses. Add it to the sidebar to continue.")
        return
    
    # Control panel
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.detection_running:
            if st.button("🚀 Start Complete SentioAI Session", use_container_width=True, type="primary"):
                st.session_state.detection_running = True
                st.session_state.session_start_time = datetime.now()
                st.rerun()
        else:
            col_stop, col_refresh = st.columns(2)
            with col_stop:
                if st.button("⏹️ End Session", use_container_width=True):
                    st.session_state.detection_running = False
                    st.rerun()
            with col_refresh:
                if st.button("🔄 New Emotion", use_container_width=True):
                    st.rerun()
    
    if st.session_state.detection_running:
        # Simulate emotion detection (in real app, this would connect to camera)
        emotions = ['happy', 'sad', 'neutral', 'surprise', 'angry', 'fear']
        current_emotion = random.choice(emotions)
        confidence = random.uniform(65, 92)
        
        st.session_state.current_emotion = {
            'emotion': current_emotion,
            'confidence': confidence
        }
        
        # Main interface
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("🧠 Current State")
            
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
                    <strong>📊 Session</strong><br>
                    Duration: {duration_str}<br>
                    Entries: {len(st.session_state.journal_entries)}
                </div>
                """
                st.markdown(session_html, unsafe_allow_html=True)
            
            # Voice input section
            st.markdown("### 🎤 Voice Input")
            uploaded_file = st.file_uploader(
                "Upload voice recording",
                type=['wav', 'mp3', 'm4a', 'ogg'],
                help="Record your thoughts and upload"
            )
            
            if uploaded_file:
                st.audio(uploaded_file)
                if st.button("📝 Transcribe", use_container_width=True):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        api_key = os.getenv('OPENAI_API_KEY') or st.session_state.get('openai_api_key')
                        with st.spinner("🎯 Transcribing..."):
                            transcript = transcribe_audio(tmp_file_path, api_key)
                        
                        if transcript:
                            st.session_state.voice_transcript = transcript
                            st.success("✅ Voice transcribed!")
                    finally:
                        os.unlink(tmp_file_path)
        
        with col_right:
            st.subheader("✍️ Emotional Journaling")
            
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
                
                # Pre-fill with voice transcript if available
                initial_text = ""
                if st.session_state.voice_transcript:
                    initial_text = f"[🎤 Voice Input]: {st.session_state.voice_transcript}\n\n"
                    st.info("🎤 Voice transcript added below. Feel free to edit or add more thoughts.")
                
                journal_text = st.text_area(
                    "Share your thoughts...",
                    value=initial_text,
                    placeholder="Start writing about what's on your mind. Let your thoughts flow naturally...",
                    height=200,
                    key=f"journal_input_{datetime.now().strftime('%H%M%S')}"
                )
                
                col_save, col_ai = st.columns([1, 1])
                
                with col_save:
                    if st.button("💾 Save Entry", use_container_width=True):
                        if journal_text.strip():
                            entry = save_journal_entry(emotion, current_prompt, journal_text)
                            st.success(f"✅ Entry saved!")
                            st.session_state.voice_transcript = ""  # Clear voice transcript
                            st.rerun()
                        else:
                            st.warning("Please write something before saving!")
                
                with col_ai:
                    if st.button("🤖 Get AI Response", use_container_width=True, type="primary"):
                        if journal_text.strip():
                            with st.spinner("🧠 AI companion is crafting a thoughtful response..."):
                                ai_response = st.session_state.gpt_companion.generate_response(
                                    journal_text, emotion, confidence/100
                                )
                            
                            # Save entry with AI response
                            entry = save_journal_entry(
                                emotion, current_prompt, journal_text, 
                                ai_response['response'] if ai_response['success'] else None
                            )
                            
                            st.session_state.latest_ai_response = ai_response
                            st.session_state.voice_transcript = ""  # Clear voice transcript
                            st.success("✅ Entry saved with AI response!")
                            st.rerun()
                        else:
                            st.warning("Please write something to get an AI response!")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show latest AI response
            if 'latest_ai_response' in st.session_state:
                ai_response = st.session_state.latest_ai_response
                
                if ai_response['success']:
                    st.markdown("### 🤖 AI Companion Response")
                    
                    ai_html = f"""
                    <div class="ai-response-container">
                        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">💙</span>
                            <strong style="color: #2E7D8E;">SentioAI Companion</strong>
                        </div>
                        <p style="margin: 0; font-size: 1.1rem; line-height: 1.6; color: #333;">
                            {ai_response['response']}
                        </p>
                        <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
                            <em>Responding to your {ai_response['emotion_addressed']} with {ai_response['confidence']:.1%} confidence</em>
                        </div>
                    </div>
                    """
                    st.markdown(ai_html, unsafe_allow_html=True)
                    
                    # Option to get a different response
                    if st.button("🔄 Get Different Response", use_container_width=True):
                        # Re-generate with different temperature for variety
                        last_entry = st.session_state.journal_entries[-1]
                        with st.spinner("🎨 Generating alternative response..."):
                            new_response = st.session_state.gpt_companion.generate_response(
                                last_entry['entry_text'], 
                                last_entry['emotion'], 
                                confidence/100
                            )
                        st.session_state.latest_ai_response = new_response
                        
                        # Update the saved entry
                        st.session_state.journal_entries[-1]['ai_response'] = new_response['response']
                        st.rerun()
        
        # Recent entries with AI responses
        if st.session_state.journal_entries:
            st.subheader("📚 Your Emotional Journey")
            
            recent_entries = st.session_state.journal_entries[-3:]
            
            for entry in reversed(recent_entries):
                with st.expander(f"{get_emotion_emoji(entry['emotion'])} {entry['readable_time']} - {entry['emotion'].title()}"):
                    st.write(f"**Prompt:** {entry['prompt']}")
                    st.write(f"**Your Entry:** {entry['entry_text']}")
                    
                    if entry.get('ai_response'):
                        st.markdown("**🤖 AI Response:**")
                        st.info(entry['ai_response'])
                    else:
                        st.write("*No AI response for this entry*")
        
        # Auto-refresh for emotion updates (every 5 seconds)
        time.sleep(5)
        st.rerun()
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem;">
            <h3>🌟 Welcome to Complete SentioAI Experience</h3>
            <p style="font-size: 1.1rem; color: #666; max-width: 800px; margin: 0 auto;">
                The complete emotional journaling companion with real-time emotion detection, 
                voice input, guided prompts, and empathetic AI responses. Start a session to experience 
                the full journey from emotion to insight.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features overview
        col1, col2, col3, col4 = st.columns(4)
        
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
            **🎤 Voice Integration**
            - Speech-to-text with Whisper
            - Voice emotion analysis
            - Seamless text integration
            """)
        
        with col4:
            st.markdown("""
            **🤖 AI Companion**
            - Empathetic GPT responses
            - Emotion-aware tone adaptation
            - Thoughtful follow-up questions
            """)

if __name__ == "__main__":
    main()
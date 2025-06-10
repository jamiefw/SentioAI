#!/usr/bin/env python3
"""
Week 4 Fixed: SentioAI with Better UX
Fixes emotion timing, UI confusion, and user experience issues
"""

import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title="SentioAI - Emotional Journal",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import openai
import json
import tempfile
import os
from datetime import datetime
import uuid
import random

# GPT Companion Class
class EmotionalCompanion:
    def __init__(self, api_key):
        """Initialize the GPT emotional companion"""
        self.client = openai.OpenAI(api_key=api_key)
        
        self.emotion_styles = {
            'happy': {
                'tone': 'celebratory and encouraging',
                'approach': 'amplify the positive emotions and help user savor the moment'
            },
            'sad': {
                'tone': 'gentle, compassionate, and validating',
                'approach': 'acknowledge the pain, offer comfort, and gently explore the feelings'
            },
            'angry': {
                'tone': 'calm, understanding, and non-judgmental',
                'approach': 'validate the anger, help process the trigger, suggest healthy expression'
            },
            'surprise': {
                'tone': 'curious and engaged',
                'approach': 'explore the unexpected event and help process the new information'
            },
            'fear': {
                'tone': 'reassuring and grounding',
                'approach': 'acknowledge the fear, provide comfort, help ground in reality'
            },
            'disgust': {
                'tone': 'understanding and supportive',
                'approach': 'validate the strong reaction and help explore what values were violated'
            },
            'neutral': {
                'tone': 'warm and gently curious',
                'approach': 'invite deeper reflection and help uncover underlying feelings'
            }
        }
    
    def generate_response(self, journal_entry, emotion, confidence=0.8):
        """Generate empathetic response to journal entry"""
        try:
            style = self.emotion_styles.get(emotion, self.emotion_styles['neutral'])
            
            system_prompt = f"""You are SentioAI, an empathetic emotional wellness companion. A user has written a journal entry while experiencing {emotion}.

Your role:
- Be a wise, compassionate friend who truly listens
- Respond with a {style['tone']} tone
- {style['approach']}

Guidelines:
- Keep responses to 2-4 sentences (50-100 words)
- Be warm but not overly familiar
- Ask ONE thoughtful follow-up question if appropriate
- Use "I notice..." or "It sounds like..." rather than "You should..."
- Focus on emotional validation
- Be authentic and avoid clichés"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Journal entry: '{journal_entry}'"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return {
                'response': response.choices[0].message.content.strip(),
                'success': True,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'response': "I'm having trouble connecting right now, but I want you to know that what you shared matters. Sometimes taking a moment to write down our thoughts is healing in itself.",
                'success': False,
                'error': str(e)
            }

# Emotion-based prompts
EMOTION_PROMPTS = {
    'happy': [
        "What's bringing you joy today? Let's capture this positive moment...",
        "You seem bright today! What would you like to celebrate or remember?",
        "There's positive energy around you. What's going well in your life right now?"
    ],
    'sad': [
        "It looks like something is weighing on your heart. What would you like to share?",
        "Sometimes writing helps lighten emotional burdens. What's on your mind?",
        "Your feelings are valid. What's making this moment difficult for you?"
    ],
    'angry': [
        "I can sense some tension. What's frustrating you right now?",
        "Strong emotions often carry important messages. What's triggering this feeling?",
        "Sometimes writing helps process intense feelings. What's stirring this energy in you?"
    ],
    'surprise': [
        "You look surprised! What unexpected thing just happened or crossed your mind?",
        "Something seems to have caught your attention. What's the surprising moment about?",
        "Your expression suggests something unexpected. What's this new development?"
    ],
    'fear': [
        "I notice some apprehension. What's making you feel uncertain right now?",
        "Fear often points to something important to us. What's causing this worry?",
        "You seem concerned about something. What thoughts are making you feel unsettled?"
    ],
    'disgust': [
        "Something seems to be bothering you. What's creating this negative reaction?",
        "You look like something doesn't sit right with you. What's the source of this feeling?",
        "I can see something has put you off. What's causing this strong reaction?"
    ],
    'neutral': [
        "How are you feeling in this moment? What's present for you right now?",
        "Sometimes the quiet moments are perfect for reflection. What's on your mind?",
        "This feels like a good moment for some gentle self-reflection. What's stirring within you?"
    ]
}

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E7D8E;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    .emotion-card {
        background: black;
        border: 2px solid #28a745;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .emotion-display {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .confidence-display {
        font-size: 1rem;
        color: #666;
    }
    
    .prompt-container {
        background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
        border-left: 5px solid #2196F3;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-style: italic;
        font-size: 1.1rem;
        color: #333;
    }
    
    .ai-response {
        background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .voice-section {
        background: #black;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .entry-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'current_emotion' not in st.session_state:
        st.session_state.current_emotion = {'emotion': 'neutral', 'confidence': 75.0}
    if 'journal_entries' not in st.session_state:
        st.session_state.journal_entries = []
    if 'gpt_companion' not in st.session_state:
        st.session_state.gpt_companion = None
    if 'voice_transcript' not in st.session_state:
        st.session_state.voice_transcript = ""
    if 'session_active' not in st.session_state:
        st.session_state.session_active = False
    if 'latest_ai_response' not in st.session_state:
        st.session_state.latest_ai_response = None

def setup_openai():
    """Setup OpenAI API"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
    
    if api_key:
        if st.session_state.gpt_companion is None:
            st.session_state.gpt_companion = EmotionalCompanion(api_key)
        return api_key
    return None

def get_emotion_emoji(emotion):
    """Get emoji for emotion"""
    emoji_map = {
        'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
        'fear': '😨', 'disgust': '🤢', 'neutral': '😐'
    }
    return emoji_map.get(emotion, '😐')

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

def save_journal_entry(emotion, prompt, entry_text, ai_response=None):
    """Save journal entry"""
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'emotion': emotion,
        'prompt': prompt,
        'entry_text': entry_text,
        'ai_response': ai_response,
        'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y")
    }
    
    st.session_state.journal_entries.append(entry)
    
    # Save to file
    os.makedirs('data/journal_entries', exist_ok=True)
    with open('data/journal_entries/sentioai_entries.json', 'w') as f:
        json.dump(st.session_state.journal_entries, f, indent=2)
    
    return entry

def main():
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🌟 SentioAI - Emotional Journaling Companion</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">AI-powered emotional wellness through guided reflection</p>', unsafe_allow_html=True)
    
    # Setup API
    api_key = setup_openai()
    if not api_key:
        st.warning("⚠️ Please add your OpenAI API key in the sidebar to use voice transcription and AI responses.")
        return
    
    # Session controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.session_active:
            if st.button("🚀 Start New Journal Session", use_container_width=True, type="primary"):
                st.session_state.session_active = True
                # Generate initial emotion
                emotions = ['happy', 'sad', 'neutral', 'surprise', 'angry', 'fear', 'disgust']
                st.session_state.current_emotion = {
                    'emotion': random.choice(emotions),
                    'confidence': random.uniform(70, 90)
                }
                st.rerun()
        else:
            col_new, col_end = st.columns(2)
            with col_new:
                if st.button("🔄 New Emotion", use_container_width=True):
                    emotions = ['happy', 'sad', 'neutral', 'surprise', 'angry', 'fear', 'disgust']
                    st.session_state.current_emotion = {
                        'emotion': random.choice(emotions),
                        'confidence': random.uniform(70, 90)
                    }
                    st.session_state.latest_ai_response = None
                    st.rerun()
            with col_end:
                if st.button("⏹️ End Session", use_container_width=True):
                    st.session_state.session_active = False
                    st.rerun()
    
    if st.session_state.session_active:
        # Main interface with fixed layout
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            # Current emotion display
            emotion = st.session_state.current_emotion['emotion']
            confidence = st.session_state.current_emotion['confidence']
            emoji = get_emotion_emoji(emotion)
            
            st.markdown(f"""
            <div class="emotion-card">
                <div class="emotion-display">
                    {emoji} {emotion.upper()}
                </div>
                <div class="confidence-display">
                    {confidence:.1f}% confidence
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Session stats
            st.markdown(f"""
            <div style="background: black; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <strong>📊 Session Stats</strong><br>
                Entries: {len(st.session_state.journal_entries)}<br>
                Current Emotion: {emotion.title()}
            </div>
            """, unsafe_allow_html=True)
            
            # Voice input section
            st.markdown('<div class="voice-section">', unsafe_allow_html=True)
            st.markdown("### 🎤 Voice Input")
            
            uploaded_file = st.file_uploader(
                "Upload voice recording",
                type=['wav', 'mp3', 'm4a', 'ogg'],
                help="Record your thoughts and upload here"
            )
            
            if uploaded_file:
                st.audio(uploaded_file)
                if st.button("📝 Transcribe Voice", use_container_width=True):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        with st.spinner("🎯 Transcribing your voice..."):
                            transcript = transcribe_audio(tmp_file_path, api_key)
                        
                        if transcript:
                            st.session_state.voice_transcript = transcript
                            st.success("✅ Voice transcribed! It will appear in the journal box.")
                            st.rerun()
                    finally:
                        os.unlink(tmp_file_path)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_right:
            # Get emotion-based prompt
            prompts = EMOTION_PROMPTS.get(emotion, EMOTION_PROMPTS['neutral'])
            current_prompt = random.choice(prompts)
            
            # Display prompt
            st.markdown(f"""
            <div class="prompt-container">
                💭 {current_prompt}
            </div>
            """, unsafe_allow_html=True)
            
            # Journal input - SINGLE TEXT AREA
            st.markdown("### ✍️ Your Journal Entry")
            
            # Pre-fill with voice if available
            initial_text = ""
            if st.session_state.voice_transcript:
                initial_text = f"[🎤 Voice]: {st.session_state.voice_transcript}\n\n"
                st.info("🎤 Voice transcript added to your journal entry below.")
            
            # SINGLE text area - this fixes the confusion
            journal_text = st.text_area(
                "Write your thoughts here...",
                value=initial_text,
                height=200,
                placeholder="Share what's on your mind. Let your thoughts flow naturally...",
                key="main_journal_input"
            )
            
            # Action buttons
            col_save, col_ai = st.columns(2)
            
            with col_save:
                if st.button("💾 Save Entry", use_container_width=True):
                    if journal_text.strip():
                        entry = save_journal_entry(emotion, current_prompt, journal_text)
                        st.success("✅ Journal entry saved!")
                        st.session_state.voice_transcript = ""  # Clear voice
                        st.rerun()
                    else:
                        st.warning("Please write something before saving!")
            
            with col_ai:
                if st.button("🤖 Get AI Response", use_container_width=True, type="primary"):
                    if journal_text.strip():
                        with st.spinner("🧠 AI is crafting a thoughtful response..."):
                            ai_response = st.session_state.gpt_companion.generate_response(
                                journal_text, emotion, confidence/100
                            )
                        
                        # Save with AI response
                        entry = save_journal_entry(emotion, current_prompt, journal_text, 
                                                 ai_response['response'] if ai_response['success'] else None)
                        
                        st.session_state.latest_ai_response = ai_response
                        st.session_state.voice_transcript = ""  # Clear voice
                        st.success("✅ Entry saved with AI response!")
                        st.rerun()
                    else:
                        st.warning("Please write something to get an AI response!")
            
            # Show AI response if available
            if st.session_state.latest_ai_response:
                ai_resp = st.session_state.latest_ai_response
                
                st.markdown("### 🤖 AI Companion Response")
                
                if ai_resp['success']:
                    # Show the response in a clear container
                    st.success("✅ AI Response Generated")
                    
                    # Display the actual response text clearly
                    st.info(f"💙 {ai_resp['response']}")
                    
                    # Show response metadata
                    with st.expander("📊 Response Details"):
                        st.write(f"**Tokens Used:** {ai_resp.get('tokens_used', 'N/A')}")
                        st.write(f"**Emotion Addressed:** {emotion}")
                        st.write(f"**Confidence:** {confidence:.1f}%")
                    
                    # Option for different response
                    if st.button("🔄 Get Different Response", use_container_width=True):
                        if st.session_state.journal_entries:
                            last_entry = st.session_state.journal_entries[-1]
                            with st.spinner("🎨 Generating alternative response..."):
                                new_response = st.session_state.gpt_companion.generate_response(
                                    last_entry['entry_text'], emotion, confidence/100
                                )
                            st.session_state.latest_ai_response = new_response
                            if st.session_state.journal_entries:
                                st.session_state.journal_entries[-1]['ai_response'] = new_response['response']
                            st.rerun()
                
                else:
                    st.error("❌ Error generating AI response")
                    st.write(f"Error: {ai_resp.get('error', 'Unknown error')}")
                    
                    # Show fallback response
                    if 'response' in ai_resp:
                        st.info(f"💙 {ai_resp['response']}")
            
            else:
                # Show placeholder when no response yet
                st.markdown("### 🤖 AI Companion Response")
                st.info("👆 Click 'Get AI Response' above to receive a thoughtful response to your journal entry.")
        
        # Recent entries
        if st.session_state.journal_entries:
            st.markdown("---")
            st.subheader("📚 Your Recent Journal Entries")
            
            for entry in reversed(st.session_state.journal_entries[-3:]):
                with st.expander(f"{get_emotion_emoji(entry['emotion'])} {entry['readable_time']} - {entry['emotion'].title()}"):
                    st.markdown(f"**Prompt:** {entry['prompt']}")
                    st.markdown(f"**Your Entry:** {entry['entry_text']}")
                    if entry.get('ai_response'):
                        st.markdown("**🤖 AI Response:**")
                        st.info(entry['ai_response'])
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>Welcome to SentioAI</h3>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
                Your AI-powered emotional journaling companion. Get personalized prompts 
                based on your emotions and receive supportive AI responses.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **🧠 Emotion Awareness**
            - Simulated emotion detection
            - Personalized prompts
            - Emotional self-discovery
            """)
        with col2:
            st.markdown("""
            **🎤 Voice Integration**
            - Speech-to-text transcription
            - Natural voice journaling
            - Seamless text integration
            """)
        with col3:
            st.markdown("""
            **🤖 AI Companion**
            - Empathetic responses
            - Emotional validation
            - Thoughtful insights
            """)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import streamlit as st
import os
import sys
import threading
import time
import queue
import random
import uuid
from datetime import datetime
import openai
import cv2
import json
import tempfile
import plotly.express as px
import base64 # <-- NEW: Import base64 for image encoding

# --- File Path Resolution ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.join(current_script_dir, '..')
sys.path.insert(0, project_root_dir)

# --- CORRECTED: st.set_page_config() must be the very first command. ---
st.set_page_config(
    page_title="SentioAI",
    page_icon="images/sentioai.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NEW: Function to encode image to Base64 ---
def get_image_as_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# --- Inject Custom CSS for UI/UX ---
st.markdown(
    """
    <style>
    /* -------------------------- GLOBAL STYLES -------------------------- */
    /* Global fonts and text colors */
    h1, h2, h3, h4, h5, h6, strong {
        color: #2F3645;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    p, li, div, label, span {
        color: #555555;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }

    /* Streamlit-specific overrides */
    .stApp {
        transition: background-color 0.1s ease-in-out;
    }
    
    /* CORRECTED: New Header container for logo and title alignment */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .header-container h1 {
        margin: 0;
        padding-left: 10px;
        font-size: 3rem;
        font-weight: bold;
        color: white; /* CORRECTED: Title color changed to white */
    }

    .stButton > button {
        border-radius: 8px;
        border: 1px solid #ced4da;
        background-color: #f8f9fa;
        color: black;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #e9ecef;
        border-color: #adb5bd;
        color: #212529;
    }
    .stButton > button[type="primary"] {
        background-color: #4A90E2;
        color: black;
        border-color: #4A90E2;
    }
    .stButton > button[type="primary"]:hover {
        background-color: #357ABD;
        border-color: #357ABD;
        color:black;
    }

    /* -------------------------- APP PAGE STYLES -------------------------- */
    .emotion-badge {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1F2A37;
        background-color: #F0F2F6;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #e0e4e9;
    }
    
    .session-info {
        background-color: #F0F2F6;
        padding: 1rem;
        border-radius: 12px;
        margin-top: 1.5rem;
        font-size: 1rem;
        border: 1px solid #e0e4e9;
    }
    
    .prompt-container {
        font-size: 1.1rem;
        font-style: italic;
        color: #444;
        background-color: #F0F2F6;
        padding: 1rem;
        border-left: 5px solid #4A90E2;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }

    .journal-container {
        padding: 1.5rem 0;
    }
    
    .ai-response-container {
        background-color: #EBF5F8;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 2rem;
        border: 1px solid #B0D0DA;
    }
    .ai-response-container strong {
        color: #2E7D8E;
    }
    </style>
    """,
    unsafe_allow_html=True
)


import backend.app.services.database as database

try:
    from models.emotion_detection.emotion_classifier import EmotionDetector
except ImportError as e:
    st.error(f"Could not import EmotionDetector: {e}. Please ensure 'models/emotion_detection/emotion_classifier.py' exists and dependencies are installed.")
    st.stop()

# --- GPT Companion Class (No changes needed) ---
class EmotionalCompanion:
    def __init__(self, api_key):
        """Initialize the GPT emotional companion"""
        self.client = openai.OpenAI(api_key=api_key)
        self.emotion_styles = {
            'happy': {'tone': 'celebratory and encouraging', 'approach': 'amplify the positive emotions and help user savor the moment', 'avoid': 'being dismissive or bringing up potential problems'},
            'sad': {'tone': 'gentle, compassionate, and validating', 'approach': 'acknowledge the pain, offer comfort, and gently explore the feelings', 'avoid': 'trying to fix or minimize the sadness'},
            'angry': {'tone': 'calm, understanding, and non-judgmental', 'approach': 'validate the anger, help process the trigger', 'avoid': 'escalating the anger or being dismissive'},
            'surprise': {'tone': 'curious and engaged', 'approach': 'explore the unexpected event and help process the new information', 'avoid': 'being overwhelming or dismissive of the surprise'},
            'fear': {'tone': 'reassuring and grounding', 'approach': 'acknowledge the fear, provide comfort, help ground in reality', 'avoid': 'minimizing the fear or being overly optimistic'},
            'disgust': {'tone': 'understanding and supportive', 'approach': 'validate the strong reaction and help explore what values were violated', 'avoid': 'judging the reaction or the source of disgust'},
            'neutral': {'tone': 'warm and gently curious', 'approach': 'invite deeper reflection and help uncover underlying feelings', 'avoid': 'being too probing or assuming something is wrong'}
        }
    
    def generate_system_prompt(self, emotion, confidence):
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
        try:
            system_prompt = self.generate_system_prompt(emotion, confidence)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Journal entry: '{journal_entry}'"}],
                max_tokens=150, temperature=0.7, presence_penalty=0.1, frequency_penalty=0.1
            )
            return {'response': response.choices[0].message.content.strip(), 'emotion_addressed': emotion, 'confidence': confidence, 'success': True, 'tokens_used': response.usage.total_tokens}
        except Exception as e:
            return {'response': "I'm having trouble connecting right now, but I want you to know that what you shared matters. Sometimes taking a moment to write down our thoughts is healing in itself.", 'error': str(e), 'success': False, 'fallback': True}

# --- Emotion-based prompts (No changes needed) ---
EMOTION_PROMPTS = {
    'happy': ["What's bringing you joy today? Let's capture this positive moment...", "You seem bright today! What would you like to celebrate or remember?"],
    'sad': ["It looks like something is weighing on your heart. What would you like to share?", "Sometimes writing helps lighten emotional burdens. What's on your mind?"],
    'angry': ["I can sense some tension. What's frustrating you right now?", "Strong emotions often carry important messages. What's triggering this feeling?"],
    'surprise': ["You look surprised! What unexpected thing just happened or crossed your mind?", "Something seems to have caught your attention. What's the surprising moment about?"],
    'fear': ["I notice some apprehension. What's making you feel uncertain right now?", "Fear often points to something important to us. What's causing this worry?"],
    'disgust': ["Something seems to be bothering you. What's creating this negative reaction?", "You look like something doesn't sit right with you. What's the source of this feeling?"],
    'neutral': ["How are you feeling in this moment? What's present for you right now?", "Sometimes the quiet moments are perfect for reflection.", "You seem calm and centered. What would you like to explore or share today?"]
}

# Emotion colors for visual representation
EMOTION_COLORS = {
    'happy': "#FDF1B9",  # Light yellow
    'sad': "#C7E5F8",    # Light blue
    'angry': "#F6B3BC",  # Very light red
    'surprise': "#F7E1C7", # Light orange
    'fear': "#EED9F1",   # Light purple
    'disgust': "#DFF0D8", # Very light green
    'neutral': "#E0E0E0" # Light grey
}

def _get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def run_camera_detection(detector_instance, stop_event_for_thread, output_queue):
    cap = None 
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            stop_event_for_thread.set() 
            output_queue.put({'status': 'error', 'message': "Webcam could not be opened. Please check connections/permissions."})
            return
        if not detector_instance:
            stop_event_for_thread.set()
            output_queue.put({'status': 'error', 'message': "Emotion detection engine not initialized."})
            return

        while not stop_event_for_thread.is_set():
            ret, frame = cap.read()
            if not ret:
                stop_event_for_thread.set()
                output_queue.put({'status': 'error', 'message': "Failed to read frame from webcam."})
                break 
            try:
                emotion_data = detector_instance.detect_emotion(frame)
            except Exception as detector_e:
                emotion_data = None 
                output_queue.put({'status': 'warning', 'message': f"Emotion detection temporarily failed: {detector_e}"})

            if emotion_data and 'emotion' in emotion_data and 'confidence' in emotion_data:
                output_queue.put({'status': 'success', 'emotion': emotion_data['emotion'], 'confidence': emotion_data['confidence'], 'timestamp': _get_timestamp()})
            time.sleep(0.05)
    except Exception as e:
        stop_event_for_thread.set()
        output_queue.put({'status': 'critical_error', 'message': f"Critical camera thread error: {e}"})
    finally:
        if cap and cap.isOpened(): 
            cap.release()
        stop_event_for_thread.set() 

def initialize_session_state():
    if 'emotion_detector' not in st.session_state: st.session_state.emotion_detector = None
    if 'gpt_companion' not in st.session_state: st.session_state.gpt_companion = None
    if 'detection_running' not in st.session_state: st.session_state.detection_running = False
    if 'current_emotion' not in st.session_state: st.session_state.current_emotion = {'emotion': 'neutral', 'confidence': 0.0}
    if 'session_start_time' not in st.session_state: st.session_state.session_start_time = None
    if 'journal_entries' not in st.session_state: st.session_state.journal_entries = []
    if 'current_prompt' not in st.session_state: st.session_state.current_prompt = ""
    if 'voice_transcript' not in st.session_state: st.session_state.voice_transcript = ""
    if 'camera_thread' not in st.session_state: st.session_state.camera_thread = None
    if 'detector_instance_created' not in st.session_state: st.session_state.detector_instance_created = False
    if 'stop_event' not in st.session_state: st.session_state.stop_event = None
    if 'emotion_queue' not in st.session_state: st.session_state.emotion_queue = queue.Queue()
    if 'display_prompt_text' not in st.session_state: st.session_state.display_prompt_text = ""
    if 'prompt_is_fresh' not in st.session_state: st.session_state.prompt_is_fresh = True
    if 'journal_input_value' not in st.session_state: st.session_state.journal_input_value = ""

def setup_apis():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input("OpenAI API Key", type="password", key="openai_api_key_input")
    if api_key:
        st.session_state.openai_api_key = api_key 
        if st.session_state.gpt_companion is None:
            st.session_state.gpt_companion = EmotionalCompanion(api_key)
        return True
    return False

def get_emotion_emoji(emotion):
    return ''

def get_emotion_prompt(emotion):
    prompts = EMOTION_PROMPTS.get(emotion, EMOTION_PROMPTS['neutral'])
    return random.choice(prompts)

def transcribe_audio(audio_file_path, api_key):
    try:
        with open(audio_file_path, 'rb') as audio_file:
            client = openai.OpenAI(api_key=api_key)
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="en")
        return transcript.text
    except Exception as e:
        st.error(f"Voice transcription failed: {e}")
        return None

def save_journal_entry(emotion, prompt, entry_text, ai_response=None, voice_data=None):
    entry = {
        'id': str(uuid.uuid4()), 'timestamp': datetime.now().isoformat(), 'emotion': emotion,
        'confidence': st.session_state.current_emotion.get('confidence', 0.0), 'prompt': prompt,
        'entry_text': entry_text, 'ai_response': ai_response, 'voice_data': voice_data,
        'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y"), 'has_ai_response': ai_response is not None
    }
    db_insertion_successful = database.insert_journal_entry(entry)
    if db_insertion_successful:
        st.success(f"Entry saved successfully! ({entry['emotion'].title()})")
        st.session_state.journal_entries.append(entry) 
        return True
    else:
        st.error("Failed to save entry to database. Check terminal for details.")
        return False

def main():
    initialize_session_state() 
    database.create_tables() 
    
    # CORRECTED: Consolidated header block for logo and title
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])
    with header_col2:
        logo_path = os.path.join(current_script_dir, "images", "sentioai.png")
        if os.path.exists(logo_path):
            # NEW: Manually read and encode the image to embed it in HTML
            img_b64 = get_image_as_base64(logo_path)
            st.markdown(f"""
                <div class="header-container">
                    <img src="data:image/png;base64,{img_b64}" width="60" />
                    <h1>SentioAI</h1>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"Error: Logo file not found at {logo_path}")

    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Emotion detection • Guided prompts • Voice input • AI companion responses</p>', unsafe_allow_html=True)
    
    if not setup_apis():
        st.warning("OpenAI API key required for voice transcription and AI responses. Add it to the sidebar to continue.")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.detection_running:
            if st.button("Start Complete SentioAI Session", use_container_width=True, type="primary"):
                if not st.session_state.detector_instance_created:
                    st.session_state.emotion_detector = EmotionDetector(smoothing_window=8, detection_interval=15.0)
                    st.session_state.detector_instance_created = True
                
                st.session_state.stop_event = threading.Event()
                st.session_state.stop_event.clear() 
                st.session_state.emotion_queue = queue.Queue()
                st.session_state.detection_running = True 
                st.session_state.session_start_time = datetime.now()
                st.session_state.prompt_is_fresh = True
                st.session_state.journal_input_value = ""

                if st.session_state.camera_thread is None or not st.session_state.camera_thread.is_alive():
                    st.session_state.camera_thread = threading.Thread(
                        target=run_camera_detection, 
                        args=(st.session_state.emotion_detector, st.session_state.stop_event, st.session_state.emotion_queue),
                        daemon=True
                    )
                    st.session_state.camera_thread.start()
                st.rerun() 
        else:
            col_stop, col_refresh_prompt = st.columns(2)
            with col_stop:
                if st.button("End Session", use_container_width=True):
                    if st.session_state.stop_event:
                        st.session_state.stop_event.set()
                    if st.session_state.camera_thread and st.session_state.camera_thread.is_alive():
                        st.session_state.camera_thread.join(timeout=5)
                    
                    st.session_state.detection_running = False 
                    st.session_state.emotion_detector = None 
                    st.session_state.camera_thread = None 
                    st.session_state.detector_instance_created = False 
                    st.session_state.stop_event = None 
                    st.session_state.prompt_is_fresh = True
                    st.session_state.journal_input_value = ""
                    st.session_state.display_prompt_text = ""
                    
                    while not st.session_state.emotion_queue.empty(): 
                        try:
                            st.session_state.emotion_queue.get_nowait()
                        except queue.Empty:
                            break
                    st.rerun()
            with col_refresh_prompt:
                if st.button("Get New Prompt", use_container_width=True):
                    st.session_state.prompt_is_fresh = True
                    st.rerun()
    
    if st.session_state.detection_running:
        try:
            while True: 
                update_data = st.session_state.emotion_queue.get_nowait()
                if update_data['status'] == 'success':
                    st.session_state.current_emotion = {'emotion': update_data['emotion'], 'confidence': update_data['confidence']}
                elif update_data['status'] in ('error', 'critical_error'):
                    st.error(f"Error from camera thread: {update_data['message']}")
                    st.session_state.detection_running = False 
                elif update_data['status'] == 'warning':
                    st.warning(f"Camera thread warning: {update_data['message']}")
        except queue.Empty:
            pass
        except Exception as e:
            st.error(f"Error processing queue data in main thread: {e}")
            st.session_state.detection_running = False 

        current_emotion_for_theme = st.session_state.current_emotion.get('emotion', 'neutral')
        background_color = EMOTION_COLORS.get(current_emotion_for_theme, EMOTION_COLORS['neutral'])
        
        st.markdown(f"<style>.stApp {{ background-color: {background_color}; }}</style>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("Current State")
            
            emotion = st.session_state.current_emotion.get('emotion', 'neutral')
            confidence = st.session_state.current_emotion.get('confidence', 0.0)
            
            emotion_html = f"""
            <div class="emotion-badge emotion-{emotion}">
                {emotion.upper()}
                <br>
                <small>{confidence:.1f}% confidence</small>
            </div>
            """
            st.markdown(emotion_html, unsafe_allow_html=True)
            
            st.write("Camera active in background, detecting emotions...")

            if st.session_state.session_start_time:
                duration = datetime.now() - st.session_state.session_start_time
                duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                
                session_html = f"""
                <div class="session-info">
                    <strong>Session</strong><br>
                    Duration: {duration_str}<br>
                    Entries: {len(st.session_state.journal_entries)}
                </div>
                """
                st.markdown(session_html, unsafe_allow_html=True)
            
            st.markdown("### Voice Input")
            uploaded_file = st.file_uploader("Upload voice recording", type=['wav', 'mp3', 'm4a', 'ogg'], key="voice_uploader")
            
            if uploaded_file:
                st.audio(uploaded_file)
                if st.button("Transcribe Voice", use_container_width=True): 
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    try:
                        api_key = st.session_state.get('openai_api_key') 
                        if api_key:
                            with st.spinner("Transcribing..."):
                                transcript = transcribe_audio(tmp_file_path, api_key)
                            if transcript:
                                st.session_state.voice_transcript = transcript
                                st.session_state.journal_input_value = f"[Voice Input]: {transcript}\n\n"
                                st.success("Voice transcribed!")
                            else:
                                st.error("Transcription failed. Check API key or audio file.")
                        else:
                            st.warning("Please provide OpenAI API key to transcribe voice.")
                    finally:
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
        
        with col_right:
            st.subheader("Emotional Journaling")
            
            if st.session_state.prompt_is_fresh:
                st.session_state.display_prompt_text = get_emotion_prompt(emotion)
                st.session_state.prompt_is_fresh = False
            
            prompt_html = f"""
            <div class="prompt-container">
                {st.session_state.display_prompt_text}
            </div>
            """
            st.markdown(prompt_html, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="journal-container">', unsafe_allow_html=True)
                
                journal_text = st.text_area(
                    "Share your thoughts...",
                    value=st.session_state.journal_input_value,
                    placeholder="Start writing about what's on your mind. Let your thoughts flow naturally...",
                    height=200,
                    key="main_journal_input",
                    on_change=lambda: st.session_state.update(journal_input_value=st.session_state.main_journal_input)
                )
                
                col_save, col_ai = st.columns([1, 1])
                
                with col_save:
                    if st.button("Save Entry", use_container_width=True):
                        entry_content = st.session_state.journal_input_value.strip()
                        if entry_content:
                            save_journal_entry(emotion, st.session_state.display_prompt_text, entry_content)
                            st.session_state.voice_transcript = ""  
                            st.session_state.journal_input_value = ""
                            st.session_state.prompt_is_fresh = True
                            st.rerun()
                        else:
                            st.warning("Please write something before saving!")
                
                with col_ai:
                    if st.button("Get AI Response", use_container_width=True, type="primary"):
                        entry_content = st.session_state.journal_input_value.strip()
                        if entry_content:
                            with st.spinner("AI companion is crafting a thoughtful response..."):
                                ai_response = st.session_state.gpt_companion.generate_response(entry_content, emotion, confidence/100)
                            
                            save_journal_entry(emotion, st.session_state.display_prompt_text, entry_content, ai_response['response'] if ai_response['success'] else None)
                            
                            st.session_state.latest_ai_response = ai_response
                            st.session_state.voice_transcript = ""  
                            st.session_state.journal_input_value = ""
                            st.session_state.prompt_is_fresh = True
                            st.success("Entry saved with AI response!")
                            st.rerun()
                        else:
                            st.warning("Please write something to get an AI response!")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            if 'latest_ai_response' in st.session_state and st.session_state.latest_ai_response['success']:
                ai_response = st.session_state.latest_ai_response
                st.markdown("### AI Companion Response")
                ai_html = f"""
                <div class="ai-response-container">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <strong style="color: #2E7D8E;">SentioAI Companion</strong>
                    </div>
                    <p style="margin: 0; font-size: 1.1rem; line-height: 1.6; color: #333;">
                        {ai_response['response']}
                    </p>
                    <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
                        <em>Responding to your {ai_response['emotion_addressed']} with {ai_response['confidence']:.1f}% confidence</em>
                    </div>
                </div>
                """
                st.markdown(ai_html, unsafe_allow_html=True)
                
                if st.button("Get Different Response", use_container_width=True, key="get_diff_ai_response"):
                    if st.session_state.journal_entries:
                        last_entry = st.session_state.journal_entries[-1]
                        with st.spinner("Generating alternative response..."):
                            entry_emotion = last_entry['emotion']
                            entry_confidence = last_entry['confidence'] if 'confidence' in last_entry else confidence 
                            new_response = st.session_state.gpt_companion.generate_response(last_entry['entry_text'], entry_emotion, entry_confidence/100)
                        st.session_state.latest_ai_response = new_response
                        if new_response['success']:
                            st.session_state.journal_entries[-1]['ai_response'] = new_response['response']
                        st.rerun()
                    else:
                        st.warning("No previous entry to generate a different response for.")
            elif 'latest_ai_response' in st.session_state and not st.session_state.latest_ai_response['success']:
                st.error("Error generating AI response.")
                st.write(st.session_state.latest_ai_response.get('error', 'Unknown error.'))

        if st.session_state.journal_entries:
            st.subheader("Your Emotional Journey")
            recent_entries = st.session_state.journal_entries[-3:]
            for entry in reversed(recent_entries):
                with st.expander(f"{entry['readable_time']} - {entry['emotion'].title()}"):
                    st.write(f"**Prompt:** {entry['prompt']}")
                    st.write(f"**Your Entry:** {entry['entry_text']}")
                    if entry.get('ai_response'):
                        st.markdown("**AI Response:**")
                        st.info(entry['ai_response'])
                    else:
                        st.write("*No AI response for this entry*")
        
        if st.session_state.detection_running:
            time.sleep(2) 
            st.rerun()
    
    else:
        # --- Landing Page UI ---
        st.markdown(
            """
            <style>
            /* Keyframes for the vibrant, gradient animation */
            @keyframes vibrant-gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            .stApp {
                background: linear-gradient(135deg, #0C1A30, #7dc7c7, #2A2A5A, #4f345c);
                background-size: 400% 400%;
                animation: vibrant-gradient 8s ease infinite;
            }
            /* CORRECTED: Set text color for landing page titles/text to white for readability */
            .stApp .header-container h1, .stApp p, .stApp strong, .stApp h3 {
                color: #F0F0F0 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <h3>Welcome to The SentioAI Experience</h3>
            <p style="font-size: 1.1rem; max-width: 800px; margin: 0 auto;">
                The complete emotional journaling companion with real-time emotion detection, 
                voice input, guided prompts, and empathetic AI responses. Start a session to experience 
                the full journey from emotion to insight.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            **Emotion Detection**
            - Real-time facial emotion recognition
            - 7 core emotions detected
            - Confidence scoring
            """)
        
        with col2:
            st.markdown("""
            **Smart Prompts**
            - Emotion-driven writing prompts
            - Contextual reflection questions
            - Supportive guidance
            """)
        
        with col3:
            st.markdown("""
            **Voice Integration**
            - Speech-to-text with Whisper
            - Voice emotion analysis
            - Seamless text integration
            """)
        
        with col4:
            st.markdown("""
            **AI Companion**
            - Empathetic GPT responses
            - Emotion-aware tone adaptation
            - Thoughtful follow-up questions
            """)
        st.markdown("---")
        st.subheader("Your Emotional Insights")

        with st.expander("View Your Emotional Data & Analytics"):
            all_entries = database.get_all_journal_entries() 
            if all_entries:
                import pandas as pd
                df = pd.DataFrame(all_entries)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)

                st.write("### All Journal Entries")
                display_cols = ['readable_time', 'emotion', 'confidence', 'prompt', 'entry_text', 'ai_response'] 
                existing_display_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[existing_display_cols], use_container_width=True)

                st.write("---") 
                st.write("### Emotional Timeline")
                if not df.empty:
                    try:
                        fig_timeline = px.line(df, x='timestamp', y='confidence', color='emotion', title='Dominant Emotion Confidence Over Time', labels={'timestamp': 'Date & Time', 'confidence': 'Confidence (%)', 'emotion': 'Emotion'}, hover_data=['emotion', 'confidence']) 
                        fig_timeline.update_layout(hovermode="x unified") 
                        st.plotly_chart(fig_timeline, use_container_width=True)
                        st.write("### Emotion Breakdown")
                        emotion_counts = df['emotion'].value_counts().reset_index()
                        emotion_counts.columns = ['Emotion', 'Count']
                        fig_bar = px.bar(emotion_counts, x='Emotion', y='Count', title='Overall Emotion Breakdown', color='Emotion')
                        st.plotly_chart(fig_bar, use_container_width=True)
                    except TypeError as e:
                        st.error(f"Error generating Plotly chart: {e}. This usually means there's a non-JSON serializable object (like bytes) in your data.")
                else:
                    st.info("No data available to generate charts. Save some entries first!")
            else:
                st.info("No journal entries found in the database yet. Start a session and save some to see your insights here!")

if __name__ == "__main__":
    main()
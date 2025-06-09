#!/usr/bin/env python3
"""
Week 3 Completion: Voice Input Integration for SentioAI
Adds speech-to-text functionality using OpenAI Whisper
"""

import streamlit as st
import openai
import tempfile
import os
from datetime import datetime
import json
import uuid
import sys

# Add models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models', 'voice_analysis'))

# Voice processing functions
def setup_openai_api():
    """Setup OpenAI API key"""
    # You'll need to add your OpenAI API key
    # Option 1: Environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Option 2: Streamlit secrets (recommended for deployment)
    if not api_key and hasattr(st, 'secrets'):
        api_key = st.secrets.get('OPENAI_API_KEY')
    
    # Option 3: Direct input (for testing)
    if not api_key:
        api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")
    
    if api_key:
        openai.api_key = api_key
        return True
    return False

def transcribe_audio(audio_file_path):
    """Transcribe audio using OpenAI Whisper"""
    try:
        with open(audio_file_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="en"  # You can make this dynamic
            )
        return transcript.text
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None

def analyze_voice_emotion(audio_file_path):
    """
    Analyze emotional tone from voice (placeholder implementation)
    In a full implementation, this would use audio analysis libraries
    """
    # This is a placeholder - real implementation would analyze:
    # - Pitch variations (high = excited/stressed, low = sad/calm)
    # - Speech rate (fast = anxious, slow = thoughtful)
    # - Voice intensity (loud = angry/happy, quiet = sad/reflective)
    
    import random
    
    # Simulate voice emotion analysis
    voice_emotions = {
        'tone': random.choice(['energetic', 'calm', 'tense', 'flat', 'shaky']),
        'pace': random.choice(['fast', 'normal', 'slow']),
        'intensity': random.choice(['high', 'medium', 'low']),
        'confidence': random.uniform(0.6, 0.9)
    }
    
    return voice_emotions

# Updated journaling interface with voice integration
def enhanced_journaling_interface():
    """Enhanced journaling interface with voice input"""
    
    st.markdown("### 🎤 Voice Journaling")
    
    # Check OpenAI API setup
    if not setup_openai_api():
        st.warning("⚠️ OpenAI API key required for voice transcription. Add it to continue.")
        st.info("""
        **To enable voice input:**
        1. Get an OpenAI API key from https://platform.openai.com/api-keys
        2. Add it to the sidebar or set OPENAI_API_KEY environment variable
        3. Refresh the page
        """)
        return None
    
    # Voice input section
    col_record, col_upload = st.columns(2)
    
    with col_record:
        st.markdown("**🔴 Record Audio**")
        
        # Audio recorder component (using streamlit-audio-recorder if available)
        try:
            from streamlit_audio_recorder import st_audiorec
            
            audio_bytes = st_audiorec()
            
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                
                if st.button("📝 Transcribe Recording", use_container_width=True):
                    # Save audio to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_bytes)
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Transcribe audio
                        with st.spinner("🎯 Transcribing your voice..."):
                            transcript = transcribe_audio(tmp_file_path)
                        
                        if transcript:
                            st.success("✅ Transcription complete!")
                            
                            # Analyze voice emotion
                            voice_emotion = analyze_voice_emotion(tmp_file_path)
                            
                            # Display results
                            col_transcript, col_emotion = st.columns([2, 1])
                            
                            with col_transcript:
                                st.text_area("📝 Transcribed Text", transcript, height=100)
                                
                                if st.button("➕ Add to Journal", use_container_width=True):
                                    # Add transcribed text to session state for use in main journal
                                    if 'voice_transcript' not in st.session_state:
                                        st.session_state.voice_transcript = ""
                                    st.session_state.voice_transcript += f"\n{transcript}"
                                    st.success("Added to journal input!")
                            
                            with col_emotion:
                                st.markdown("**🎵 Voice Analysis**")
                                st.write(f"Tone: {voice_emotion['tone']}")
                                st.write(f"Pace: {voice_emotion['pace']}")
                                st.write(f"Energy: {voice_emotion['intensity']}")
                    
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
        
        except ImportError:
            st.info("📱 **Browser Voice Recording**")
            st.markdown("""
            For live voice recording, install the audio recorder:
            ```bash
            pip install streamlit-audio-recorder
            ```
            Then restart the app.
            """)
    
    with col_upload:
        st.markdown("**📁 Upload Audio File**")
        
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'm4a', 'ogg'],
            help="Upload a voice recording to transcribe"
        )
        
        if uploaded_file:
            st.audio(uploaded_file)
            
            if st.button("📝 Transcribe Upload", use_container_width=True):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                try:
                    with st.spinner("🎯 Transcribing uploaded audio..."):
                        transcript = transcribe_audio(tmp_file_path)
                    
                    if transcript:
                        st.success("✅ Transcription complete!")
                        
                        # Analyze voice emotion
                        voice_emotion = analyze_voice_emotion(tmp_file_path)
                        
                        # Display results
                        st.text_area("📝 Transcribed Text", transcript, height=100)
                        
                        col_add, col_emotion = st.columns([1, 1])
                        
                        with col_add:
                            if st.button("➕ Add to Journal Entry", use_container_width=True):
                                if 'voice_transcript' not in st.session_state:
                                    st.session_state.voice_transcript = ""
                                st.session_state.voice_transcript += f"\n{transcript}"
                                st.success("Added to journal!")
                        
                        with col_emotion:
                            with st.expander("🎵 Voice Analysis"):
                                st.write(f"**Tone:** {voice_emotion['tone']}")
                                st.write(f"**Pace:** {voice_emotion['pace']}")
                                st.write(f"**Energy:** {voice_emotion['intensity']}")
                                st.write(f"**Confidence:** {voice_emotion['confidence']:.1%}")
                
                finally:
                    os.unlink(tmp_file_path)

def save_voice_enhanced_entry(emotion, prompt, entry_text, voice_data=None):
    """Save journal entry with voice data"""
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'emotion': emotion,
        'prompt': prompt,
        'entry_text': entry_text,
        'voice_data': voice_data,
        'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y"),
        'has_voice': voice_data is not None
    }
    
    if 'journal_entries' not in st.session_state:
        st.session_state.journal_entries = []
    
    st.session_state.journal_entries.append(entry)
    
    # Save to file
    os.makedirs('data/journal_entries', exist_ok=True)
    with open('data/journal_entries/session_entries.json', 'w') as f:
        json.dump(st.session_state.journal_entries, f, indent=2)
    
    return entry

# Instructions for setting up voice features
def show_voice_setup_instructions():
    """Show setup instructions for voice features"""
    
    with st.expander("🛠️ Voice Feature Setup Instructions"):
        st.markdown("""
        ### Setting Up Voice Input
        
        **1. Install Dependencies:**
        ```bash
        pip install openai streamlit-audio-recorder
        ```
        
        **2. Get OpenAI API Key:**
        - Go to https://platform.openai.com/api-keys
        - Create a new API key
        - Add it to your environment variables or enter it in the sidebar
        
        **3. Test Voice Input:**
        - Use the "Record Audio" section to record directly in browser
        - Or upload an audio file (WAV, MP3, M4A, OGG)
        - Transcribed text will appear and can be added to your journal
        
        **4. Voice Emotion Analysis:**
        - Currently simulated (shows random voice characteristics)
        - Future versions will include real audio emotion analysis
        
        **Privacy Note:** Audio files are temporarily processed and then deleted.
        """)

# Integration function to add to main journaling interface
def add_voice_to_journal_input():
    """Add voice transcript to main journal input"""
    if 'voice_transcript' in st.session_state and st.session_state.voice_transcript:
        st.info("🎤 Voice transcript available! Click to add to your journal entry.")
        
        if st.button("📝 Insert Voice Transcript"):
            current_text = st.session_state.get('journal_input', '')
            combined_text = f"{current_text}\n\n[Voice Input:]\n{st.session_state.voice_transcript.strip()}"
            st.session_state.journal_input = combined_text
            st.session_state.voice_transcript = ""  # Clear after use
            st.success("Voice transcript added to journal entry!")
            st.rerun()

def main():
    st.title("🎤 SentioAI Voice Integration Test")
    st.write("Testing speech-to-text functionality for emotional journaling")
    
    # Show setup instructions
    show_voice_setup_instructions()
    
    # Main voice interface
    enhanced_journaling_interface()
    
    # Test the voice integration
    st.markdown("---")
    st.markdown("### 🧪 Test Voice Integration")
    st.write("This interface tests the voice input functionality that will be integrated into the main journaling app.")

if __name__ == "__main__":
    main()

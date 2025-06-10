#!/usr/bin/env python3
"""
Week 3: Simplified Voice Integration for SentioAI
Uses file upload for voice input (no live recording dependency issues)
"""

import streamlit as st
import openai
import tempfile
import os
from datetime import datetime
import json
import uuid

def setup_openai_api():
    """Setup OpenAI API key"""
    # Option 1: Environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Option 2: Streamlit sidebar input
    if not api_key:
        api_key = st.sidebar.text_input("🔑 Enter OpenAI API Key", type="password")
    
    if api_key:
        openai.api_key = api_key
        return True
    return False

def transcribe_audio(audio_file_path):
    """Transcribe audio using OpenAI Whisper"""
    try:
        with open(audio_file_path, 'rb') as audio_file:
            client = openai.OpenAI()
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        return transcript.text
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None

def analyze_voice_emotion_placeholder():
    """Placeholder voice emotion analysis"""
    import random
    
    voice_emotions = {
        'tone': random.choice(['energetic', 'calm', 'tense', 'flat', 'warm']),
        'pace': random.choice(['fast', 'normal', 'slow']),
        'energy': random.choice(['high', 'medium', 'low']),
        'confidence': random.uniform(0.6, 0.9)
    }
    
    return voice_emotions

def voice_journaling_interface():
    """Voice input interface for journaling"""
    
    st.markdown("### 🎤 Voice Input for Journaling")
    
    # Check OpenAI API setup
    if not setup_openai_api():
        st.warning("⚠️ OpenAI API key required for voice transcription.")
        with st.expander("📋 How to get an API key"):
            st.markdown("""
            1. Go to https://platform.openai.com/api-keys
            2. Sign up or log in to OpenAI
            3. Create a new API key
            4. Copy it and paste in the sidebar
            5. Refresh this page
            """)
        return None
    
    st.success("✅ OpenAI API connected! Ready for voice transcription.")
    
    # File upload method
    st.markdown("**📁 Upload Voice Recording**")
    st.info("💡 **Tip**: Use your phone's voice recorder app, then upload the file here!")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file to transcribe",
        type=['wav', 'mp3', 'm4a', 'ogg', 'flac'],
        help="Record using your phone or computer, then upload here"
    )
    
    if uploaded_file:
        st.audio(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🎯 Transcribe Audio", use_container_width=True, type="primary"):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                try:
                    with st.spinner("🎯 Transcribing your voice... This may take a few seconds."):
                        transcript = transcribe_audio(tmp_file_path)
                    
                    if transcript:
                        st.success("✅ Transcription complete!")
                        
                        # Show transcribed text
                        st.markdown("**📝 Transcribed Text:**")
                        transcript_container = st.container()
                        with transcript_container:
                            st.write(f'"{transcript}"')
                        
                        # Voice emotion analysis (placeholder)
                        voice_emotion = analyze_voice_emotion_placeholder()
                        
                        # Add to journal session
                        if st.button("➕ Add to Journal Entry", use_container_width=True):
                            if 'voice_transcript' not in st.session_state:
                                st.session_state.voice_transcript = ""
                            
                            # Add with voice indicator
                            st.session_state.voice_transcript += f"\n\n[🎤 Voice Input]: {transcript}"
                            st.success("Voice transcript added! Go back to the main journal to see it.")
                            st.balloons()
                
                except Exception as e:
                    st.error(f"Error during transcription: {e}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
        
        with col2:
            # Show voice analysis
            if uploaded_file:
                with st.expander("🎵 Voice Analysis (Preview)"):
                    voice_emotion = analyze_voice_emotion_placeholder()
                    st.write(f"**Tone:** {voice_emotion['tone']}")
                    st.write(f"**Pace:** {voice_emotion['pace']}")
                    st.write(f"**Energy:** {voice_emotion['energy']}")
                    st.progress(voice_emotion['confidence'])
                    st.caption(f"Confidence: {voice_emotion['confidence']:.1%}")
    
    # Instructions
    with st.expander("📱 How to Record Audio"):
        st.markdown("""
        **On iPhone:**
        1. Open "Voice Memos" app
        2. Tap record, speak your thoughts
        3. Stop and save the recording
        4. Share/export as audio file
        5. Upload here
        
        **On Android:**
        1. Open "Recorder" or "Voice Recorder" app
        2. Record your journal thoughts
        3. Save as audio file
        4. Upload here
        
        **On Computer:**
        1. Use QuickTime (Mac) or Voice Recorder (Windows)
        2. Record your thoughts
        3. Save as .wav or .mp3
        4. Upload here
        
        **Tips for Better Transcription:**
        - Speak clearly and at moderate pace
        - Record in a quiet environment
        - Keep recordings under 5 minutes for faster processing
        """)

def show_voice_transcript_in_main_journal():
    """Function to integrate with main journaling interface"""
    if 'voice_transcript' in st.session_state and st.session_state.voice_transcript.strip():
        st.info("🎤 **Voice transcript ready!** Click to add to your journal entry.")
        
        with st.expander("👀 Preview Voice Transcript"):
            st.write(st.session_state.voice_transcript)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Insert Voice Transcript", use_container_width=True):
                # This would integrate with the main journal text area
                current_text = st.session_state.get('journal_input', '')
                combined_text = f"{current_text}\n{st.session_state.voice_transcript}".strip()
                st.session_state.journal_input = combined_text
                st.session_state.voice_transcript = ""  # Clear after use
                st.success("✅ Voice transcript added to journal!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Voice Transcript", use_container_width=True):
                st.session_state.voice_transcript = ""
                st.success("Voice transcript cleared.")
                st.rerun()

def main():
    st.set_page_config(
        page_title="SentioAI Voice Integration",
        page_icon="🎤",
        layout="wide"
    )
    
    st.title("🎤 SentioAI Voice Integration")
    st.write("Add your voice to emotional journaling with AI transcription")
    
    # Main voice interface
    voice_journaling_interface()
    
    # Show integration with main journal
    st.markdown("---")
    st.markdown("### 🔗 Integration with Main Journal")
    show_voice_transcript_in_main_journal()
    
    # Session state debugging (for development)
    if st.sidebar.checkbox("🔧 Show Debug Info"):
        st.sidebar.write("**Session State:**")
        st.sidebar.write(f"Voice transcript: {st.session_state.get('voice_transcript', 'None')}")

if __name__ == "__main__":
    main()

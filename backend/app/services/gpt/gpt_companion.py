#!/usr/bin/env python3
"""
Week 4: GPT Emotional Companion for SentioAI
Generates empathetic, supportive responses to journal entries based on detected emotions
"""

import openai
import streamlit as st
import json
import os
from datetime import datetime
import uuid
import time

class EmotionalCompanion:
    def __init__(self, api_key):
        """Initialize the GPT emotional companion"""
        self.client = openai.OpenAI(api_key=api_key)
        self.response_history = []
        
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
        
        base_prompt = f"""You are SentioAI, an empathetic emotional wellness companion. A user has just written a journal entry while experiencing the emotion: {emotion} (detected with {confidence:.0f}% confidence).

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
- Be authentic and avoid clichés

Remember: Your goal is to help the user feel heard, understood, and gently supported in their emotional journey."""

        return base_prompt
    
    def generate_response(self, journal_entry, emotion, confidence=0.8, voice_data=None):
        """Generate empathetic response to journal entry"""
        try:
            # Create system prompt based on emotion
            system_prompt = self.generate_system_prompt(emotion, confidence)
            
            # Prepare user message
            user_message = f"Journal entry: '{journal_entry}'"
            
            # Add voice context if available
            if voice_data:
                user_message += f"\n\nVoice characteristics: {voice_data}"
            
            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # More affordable than gpt-4
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150,
                temperature=0.7,  # Balanced creativity and consistency
                presence_penalty=0.1,  # Encourage diverse responses
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Store response for learning/improvement
            self.response_history.append({
                'timestamp': datetime.now().isoformat(),
                'emotion': emotion,
                'confidence': confidence,
                'journal_entry': journal_entry,
                'ai_response': ai_response,
                'voice_data': voice_data
            })
            
            return {
                'response': ai_response,
                'emotion_addressed': emotion,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'tokens_used': response.usage.total_tokens,
                'success': True
            }
            
        except Exception as e:
            return {
                'response': f"I'm having trouble connecting right now, but I want you to know that what you shared matters. Sometimes taking a moment to write down our thoughts is healing in itself.",
                'error': str(e),
                'success': False,
                'fallback': True
            }
    
    def get_response_variations(self, journal_entry, emotion, confidence=0.8):
        """Generate multiple response options for user to choose from"""
        responses = []
        
        # Generate 3 different response styles
        styles = ['supportive', 'reflective', 'encouraging']
        
        for style in styles:
            modified_prompt = self.generate_system_prompt(emotion, confidence)
            modified_prompt += f"\n\nResponse style: Focus on being {style} in your response."
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": modified_prompt},
                        {"role": "user", "content": f"Journal entry: '{journal_entry}'"}
                    ],
                    max_tokens=120,
                    temperature=0.8
                )
                
                responses.append({
                    'style': style,
                    'response': response.choices[0].message.content.strip(),
                    'tokens': response.usage.total_tokens
                })
                
            except Exception as e:
                responses.append({
                    'style': style,
                    'response': f"I'm here to listen and support you through this {emotion} you're experiencing.",
                    'error': str(e)
                })
        
        return responses

def create_gpt_interface():
    """Create Streamlit interface for testing GPT responses"""
    
    st.title("SentioAI - GPT Emotional Companion")
    st.write("Test the AI companion that responds to your journal entries")
    
    # Setup API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    if not api_key:
        st.warning("Please enter your OpenAI API key to test the companion")
        return
    
    # Initialize companion
    if 'companion' not in st.session_state:
        st.session_state.companion = EmotionalCompanion(api_key)
    
    st.success("✅ AI Companion ready!")
    
    # Test interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Journal Entry Test")
        
        # Emotion selection for testing
        emotion = st.selectbox(
            "Current Emotion",
            ['happy', 'sad', 'angry', 'surprise', 'fear', 'disgust', 'neutral'],
            index=6
        )
        
        confidence = st.slider("Emotion Confidence", 0.5, 1.0, 0.8, 0.1)
        
        # Journal entry input
        journal_text = st.text_area(
            "Write your journal entry",
            placeholder="Share what's on your mind... The AI will respond based on your detected emotion.",
            height=150
        )
        
        # Response options
        col_single, col_multiple = st.columns(2)
        
        with col_single:
            if st.button("Get AI Response", use_container_width=True, type="primary"):
                if journal_text.strip():
                    with st.spinner("AI is crafting a thoughtful response..."):
                        response = st.session_state.companion.generate_response(
                            journal_text, emotion, confidence
                        )
                    st.session_state.current_response = response
                else:
                    st.warning("Please write something in your journal entry")
        
        with col_multiple:
            if st.button("Get 3 Response Options", use_container_width=True):
                if journal_text.strip():
                    with st.spinner("Generating response variations..."):
                        responses = st.session_state.companion.get_response_variations(
                            journal_text, emotion, confidence
                        )
                    st.session_state.response_options = responses
                else:
                    st.warning("Please write something in your journal entry")
    
    with col2:
        st.subheader("AI Companion Response")
        
        # Show single response
        if 'current_response' in st.session_state:
            response = st.session_state.current_response
            
            if response['success']:
                st.success("AI Response Generated")
                
                # Display response in a nice container
                st.markdown(f"""
                <div style="background: #000000; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #4CAF50;">
                    <p style="margin: 0; font-size: 1.1rem; line-height: 1.6;">
                        {response['response']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Response metadata
                with st.expander("📊 Response Details"):
                    st.write(f"**Emotion Addressed:** {response['emotion_addressed']}")
                    st.write(f"**Confidence:** {response['confidence']:.1%}")
                    st.write(f"**Tokens Used:** {response.get('tokens_used', 'N/A')}")
                    st.write(f"**Generated:** {response['timestamp']}")
            else:
                st.error("❌ Error generating response")
                st.write(response.get('error', 'Unknown error'))
        
        # Show multiple response options
        if 'response_options' in st.session_state:
            st.markdown("### Response Style Options")
            
            for i, resp in enumerate(st.session_state.response_options):
                with st.expander(f"{resp['style'].title()} Response"):
                    st.write(resp['response'])
                    if 'tokens' in resp:
                        st.caption(f"Tokens: {resp['tokens']}")
    
    # Response history
    if hasattr(st.session_state.companion, 'response_history') and st.session_state.companion.response_history:
        st.subheader("Recent AI Responses")
        
        recent_responses = st.session_state.companion.response_history[-3:]
        
        for i, entry in enumerate(reversed(recent_responses)):
            with st.expander(f"Response {len(recent_responses) - i} - {entry['emotion'].title()}"):
                st.write(f"**Journal:** {entry['journal_entry'][:100]}...")
                st.write(f"**AI Response:** {entry['ai_response']}")
                st.write(f"**Emotion:** {entry['emotion']} ({entry['confidence']:.1%})")

def main():
    st.set_page_config(
        page_title="SentioAI GPT Companion",
        page_icon="🤖",
        layout="wide"
    )
    
    create_gpt_interface()
    
    # Instructions
    with st.expander("How to Test the AI Companion"):
        st.markdown("""
        **Testing the Emotional AI:**
        1. **Select an emotion** from the dropdown (simulating what would be detected)
        2. **Write a journal entry** that matches that emotion
        3. **Get AI response** - see how the AI adapts its tone and approach
        4. **Try different emotions** to see how responses change
        
        **Good Test Examples:**
        - **Happy:** "I just got promoted at work! I'm so excited about the new opportunities ahead."
        - **Sad:** "I've been feeling really lonely lately. My friends seem too busy to hang out."
        - **Angry:** "I'm so frustrated with my roommate. They never clean up after themselves."
        - **Fear:** "I have a big presentation tomorrow and I'm terrified I'll mess it up."
        
        **What to Look For:**
        - Does the AI's tone match the emotion?
        - Are responses supportive without being dismissive?
        - Do follow-up questions feel natural and helpful?
        - Are responses the right length (not too long/short)?
        """)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple Working Week 2 Interface for SentioAI
Runs emotion detection in background, shows results in terminal + simple web view
"""

import cv2
import threading
import time
import json
from datetime import datetime
import sys
import os

# Add the models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models', 'emotion_detection'))

try:
    from emotion_classifier import EmotionDetector
except ImportError:
    print("❌ Could not import EmotionDetector")
    print("Make sure you're running from the SentioAI directory")
    print("And that emotion_classifier.py exists in models/emotion_detection/")
    sys.exit(1)

class SimpleEmotionUI:
    def __init__(self):
        self.detector = EmotionDetector(smoothing_window=8, detection_interval=2.0)
        self.cap = None
        self.running = False
        self.current_emotion = {'emotion': 'neutral', 'confidence': 0.0, 'timestamp': time.time()}
        self.session_start = None
        
    def start_detection(self):
        """Start the emotion detection process"""
        print("🚀 Starting SentioAI Emotion Detection - Week 2 MVP")
        print("=" * 60)
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Error: Could not open camera")
            return False
            
        print("🎥 Camera opened successfully!")
        print("📊 Emotion detection starting...")
        print("👀 Look at your camera and try different expressions")
        print("📝 Press 'q' to quit, 's' for session summary")
        print("-" * 60)
        
        self.running = True
        self.session_start = datetime.now()
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Error: Can't receive frame")
                    break
                
                # Detect emotion
                emotion_result = self.detector.detect_emotion(frame)
                self.current_emotion = emotion_result
                
                # Display current emotion in terminal
                self.display_current_emotion(emotion_result)
                
                # Draw on frame for visual feedback
                self.draw_emotion_overlay(frame, emotion_result)
                
                # Show the frame
                cv2.imshow('SentioAI - Week 2 Emotion Detection', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.show_session_summary()
                elif key == ord('h'):
                    self.show_help()
                    
        except KeyboardInterrupt:
            print("\n⏹️  Detection stopped by user")
            
        finally:
            self.cleanup()
            
    def display_current_emotion(self, emotion_result):
        """Display current emotion in terminal"""
        emotion = emotion_result['smoothed_emotion']
        confidence = emotion_result['confidence']
        face_detected = emotion_result.get('face_detected', False)
        
        # Get emotion emoji
        emoji_map = {
            'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
            'fear': '😨', 'disgust': '🤢', 'neutral': '😐'
        }
        emoji = emoji_map.get(emotion, '😐')
        
        # Clear line and show current emotion
        current_time = datetime.now().strftime("%H:%M:%S")
        if face_detected:
            status = f"[{current_time}] {emoji} Current Emotion: {emotion.upper()} ({confidence:.1f}% confidence)"
        else:
            status = f"[{current_time}] 👤 No face detected - looking for face..."
            
        # Print with carriage return to overwrite previous line
        print(f"\r{status}", end="", flush=True)
        
    def draw_emotion_overlay(self, frame, emotion_result):
        """Draw emotion information on the video frame"""
        emotion = emotion_result['smoothed_emotion']
        confidence = emotion_result['confidence']
        face_detected = emotion_result.get('face_detected', False)
        
        # Color map for emotions
        color_map = {
            'happy': (0, 255, 0),      # Green
            'sad': (255, 0, 0),        # Blue
            'angry': (0, 0, 255),      # Red
            'surprise': (0, 255, 255), # Yellow
            'fear': (128, 0, 128),     # Purple
            'disgust': (0, 128, 128),  # Dark yellow
            'neutral': (128, 128, 128) # Gray
        }
        
        color = color_map.get(emotion, (255, 255, 255))
        
        # Add text overlay
        cv2.putText(frame, f"SentioAI - {emotion.upper()}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        if face_detected:
            cv2.putText(frame, f"Confidence: {confidence:.1f}%", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            cv2.putText(frame, "No face detected", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Session info
        if self.session_start:
            duration = datetime.now() - self.session_start
            duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"
            cv2.putText(frame, f"Session: {duration_str}", 
                       (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(frame, "Press 'q' to quit, 's' for summary, 'h' for help", 
                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def show_session_summary(self):
        """Show detailed session summary"""
        print("\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        
        if self.session_start:
            duration = datetime.now() - self.session_start
            print(f"⏱️  Session Duration: {duration.seconds // 60}m {duration.seconds % 60}s")
        
        summary = self.detector.get_session_summary()
        if isinstance(summary, dict):
            print(f"😊 Most Common Emotion: {summary['most_common_emotion'].title()}")
            print(f"📝 Total Emotions Logged: {summary['total_emotions_logged']}")
            
            print("\n📈 Emotion Breakdown:")
            for emotion, count in summary['emotion_breakdown'].items():
                percentage = (count / summary['total_emotions_logged']) * 100
                emoji_map = {
                    'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
                    'fear': '😨', 'disgust': '��', 'neutral': '😐'
                }
                emoji = emoji_map.get(emotion, '😐')
                print(f"  {emoji} {emotion.title()}: {count} times ({percentage:.1f}%)")
        
        # Show recent emotion log
        emotion_log = self.detector.get_emotion_log()
        if emotion_log:
            print(f"\n📋 Recent Emotion Timeline (last 5):")
            for entry in emotion_log[-5:]:
                emoji_map = {
                    'happy': '😊', 'sad': '😔', 'angry': '😠', 'surprise': '😲',
                    'fear': '😨', 'disgust': '🤢', 'neutral': '😐'
                }
                emoji = emoji_map.get(entry['emotion'], '😐')
                print(f"  {entry['readable_time']} - {emoji} {entry['emotion'].title()}")
        
        print("=" * 60)
        print("Press any key in the video window to continue...")
        
    def show_help(self):
        """Show help information"""
        print("\n" + "=" * 60)
        print("❓ HELP - SentioAI Week 2 Interface")
        print("=" * 60)
        print("🎥 Camera Controls:")
        print("  'q' - Quit the application")
        print("  's' - Show session summary")
        print("  'h' - Show this help")
        print("")
        print("💡 Tips:")
        print("  • Make sure your face is well-lit and visible")
        print("  • Try different expressions to test accuracy")
        print("  • Emotions are smoothed over time for stability")
        print("  • Look directly at camera for best results")
        print("")
        print("🧠 Detected Emotions:")
        print("  😊 Happy  😔 Sad  😠 Angry  😲 Surprise")
        print("  😨 Fear   🤢 Disgust   😐 Neutral")
        print("=" * 60)
        print("Press any key in the video window to continue...")
        
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Show final summary
        print("\n🎉 Week 2 Emotion Detection Complete!")
        self.show_session_summary()
        
        # Export session data
        if self.detector:
            filename = self.detector.export_emotion_log()
            print(f"💾 Session data saved to: {filename}")

def main():
    """Main function"""
    print("🧠 SentioAI - Week 2 MVP Interface")
    print("Real-time emotion detection with improved UI")
    print("")
    
    ui = SimpleEmotionUI()
    
    try:
        ui.start_detection()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure:")
        print("  - You're in the SentioAI project directory")
        print("  - Camera permissions are granted")
        print("  - DeepFace is properly installed")
    finally:
        ui.cleanup()

if __name__ == "__main__":
    main()

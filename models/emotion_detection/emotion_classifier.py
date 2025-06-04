#!/usr/bin/env python3
"""
Real-time emotion detection for SentioAI
Uses DeepFace for facial emotion recognition with smoothing
"""

import cv2
import numpy as np
from deepface import DeepFace
import time
from collections import deque
import json

class EmotionDetector:
    def __init__(self, smoothing_window=8, detection_interval=3.0):
        """
        Initialize emotion detector
        
        Args:
            smoothing_window (int): Number of predictions to average for smoothing
            detection_interval (float): Seconds between emotion detections
        """
        self.smoothing_window = smoothing_window
        self.detection_interval = detection_interval
        self.last_detection_time = 0
        
        # Store recent emotions for smoothing
        self.emotion_history = deque(maxlen=smoothing_window)
        
        # Emotion mapping - DeepFace returns these emotions
        self.emotion_labels = [
            'angry', 'disgust', 'fear', 'happy', 
            'sad', 'surprise', 'neutral'
        ]
        
        # For logging emotions over time
        self.emotion_log = []
        
        print("🧠 SentioAI Emotion Detector initialized")
        print(f"📊 Smoothing window: {smoothing_window} predictions")
        print(f"⏱️  Detection interval: {detection_interval}s")
    
    def detect_emotion(self, frame):
        """
        Detect emotion from a video frame
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            dict: Contains emotion, confidence, and smoothed result
        """
        current_time = time.time()
        
        # Only run detection at specified intervals to avoid lag
        if current_time - self.last_detection_time < self.detection_interval:
            return self.get_last_emotion()
        
        try:
            # Convert BGR to RGB for DeepFace
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Analyze emotion - DeepFace handles face detection automatically
            result = DeepFace.analyze(
                rgb_frame, 
                actions=['emotion'], 
                enforce_detection=False  # Continue even if no face detected
            )
            
            # Handle both single face and multiple faces
            if isinstance(result, list):
                result = result[0]  # Use first detected face
            
            # Extract emotion probabilities
            emotions = result['emotion']
            dominant_emotion = result['dominant_emotion']
            confidence = emotions[dominant_emotion]
            
            # Add to history for smoothing
            self.emotion_history.append({
                'emotion': dominant_emotion,
                'confidence': confidence,
                'timestamp': current_time,
                'all_emotions': emotions
            })
            
            self.last_detection_time = current_time
            
            # Get smoothed result
            smoothed_emotion = self.get_smoothed_emotion()
            
            # Log emotion every 15 seconds instead of 5
            if len(self.emotion_log) == 0 or current_time - self.emotion_log[-1]['timestamp'] >= 15.0:
                self.log_emotion(smoothed_emotion, current_time)
            
            return {
                'emotion': dominant_emotion,
                'confidence': confidence,
                'smoothed_emotion': smoothed_emotion,
                'all_emotions': emotions,
                'face_detected': True,
                'timestamp': current_time
            }
            
        except Exception as e:
            print(f"⚠️  Emotion detection error: {e}")
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'smoothed_emotion': 'neutral',
                'all_emotions': {},
                'face_detected': False,
                'timestamp': current_time,
                'error': str(e)
            }
    
    def get_smoothed_emotion(self):
        """
        Get smoothed emotion based on recent history
        
        Returns:
            str: Most common emotion from recent detections
        """
        if not self.emotion_history:
            return 'neutral'
        
        # Count occurrences of each emotion
        emotion_counts = {}
        total_weight = 0
        
        for i, entry in enumerate(self.emotion_history):
            emotion = entry['emotion']
            # Weight recent detections more heavily
            weight = (i + 1) / len(self.emotion_history)
            
            if emotion not in emotion_counts:
                emotion_counts[emotion] = 0
            emotion_counts[emotion] += weight
            total_weight += weight
        
        # Return most weighted emotion
        if emotion_counts:
            return max(emotion_counts, key=emotion_counts.get)
        return 'neutral'
    
    def get_last_emotion(self):
        """Get the last detected emotion without running new detection"""
        if self.emotion_history:
            last = self.emotion_history[-1]
            return {
                'emotion': last['emotion'],
                'confidence': last['confidence'],
                'smoothed_emotion': self.get_smoothed_emotion(),
                'all_emotions': last['all_emotions'],
                'face_detected': True,
                'timestamp': last['timestamp']
            }
        return {
            'emotion': 'neutral',
            'confidence': 0.0,
            'smoothed_emotion': 'neutral',
            'all_emotions': {},
            'face_detected': False,
            'timestamp': time.time()
        }
    
    def log_emotion(self, emotion, timestamp):
        """Log emotion for timeline tracking"""
        self.emotion_log.append({
            'emotion': emotion,
            'timestamp': timestamp,
            'readable_time': time.strftime('%H:%M:%S', time.localtime(timestamp))
        })
        print(f"📝 Logged emotion: {emotion} at {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
    
    def get_emotion_log(self):
        """Get the full emotion log"""
        return self.emotion_log
    
    def export_emotion_log(self, filename=None):
        """Export emotion log to JSON file"""
        if filename is None:
            filename = f"emotion_log_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.emotion_log, f, indent=2)
        
        print(f"💾 Emotion log exported to {filename}")
        return filename
    
    def get_session_summary(self):
        """Get summary of current session"""
        if not self.emotion_log:
            return "No emotions logged yet"
        
        # Count emotions
        emotion_counts = {}
        for entry in self.emotion_log:
            emotion = entry['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Get most common emotion
        most_common = max(emotion_counts, key=emotion_counts.get)
        session_duration = self.emotion_log[-1]['timestamp'] - self.emotion_log[0]['timestamp']
        
        return {
            'duration_minutes': round(session_duration / 60, 1),
            'total_emotions_logged': len(self.emotion_log),
            'most_common_emotion': most_common,
            'emotion_breakdown': emotion_counts,
            'session_start': self.emotion_log[0]['readable_time'],
            'session_end': self.emotion_log[-1]['readable_time']
        }


def main():
    """Test the emotion detector with live webcam"""
    print("🚀 Starting SentioAI Emotion Detection Test")
    print("=" * 50)
    
    # Initialize emotion detector with longer intervals for better accuracy
    detector = EmotionDetector(smoothing_window=8, detection_interval=2.0)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera")
        return
    
    print("🎥 Camera opened successfully!")
    print("📝 Press 'q' to quit, 's' to see session summary")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect emotion
            emotion_result = detector.detect_emotion(frame)
            
            # Draw emotion info on frame
            emotion = emotion_result['smoothed_emotion']
            confidence = emotion_result['confidence']
            face_detected = emotion_result['face_detected']
            
            # Choose color based on emotion
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
            cv2.putText(frame, f"SentioAI - Emotion: {emotion.upper()}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            if face_detected:
                cv2.putText(frame, f"Confidence: {confidence:.1f}%", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            else:
                cv2.putText(frame, "No face detected", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.putText(frame, "Press 'q' to quit, 's' for summary", 
                       (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('SentioAI Emotion Detection', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                summary = detector.get_session_summary()
                print("\n📊 Session Summary:")
                print(f"Duration: {summary['duration_minutes']} minutes")
                print(f"Most common emotion: {summary['most_common_emotion']}")
                print(f"Emotions logged: {summary['total_emotions_logged']}")
                print(f"Breakdown: {summary['emotion_breakdown']}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Detection interrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Show final summary
        summary = detector.get_session_summary()
        if isinstance(summary, dict):
            print("\n🎉 Final Session Summary:")
            print(f"⏱️  Duration: {summary['duration_minutes']} minutes")
            print(f"😊 Most common emotion: {summary['most_common_emotion']}")
            print(f"📊 Total emotions logged: {summary['total_emotions_logged']}")
            
            # Export log
            filename = detector.export_emotion_log()
            print(f"💾 Session saved to: {filename}")


if __name__ == "__main__":
    main()
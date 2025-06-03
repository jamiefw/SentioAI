"""
Basic camera test script for Sentio-AI
Tests if OpenCV can access the webcam successfully
"""

import cv2
import sys

def test_camera():
    """Test basic webcam functionality"""
    print("Testing camera access...")
    
    # Try to initialize the camera (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print(" Error: Could not open camera")
        print(" Try these solutions:")
        print("   - Check if another app is using the camera")
        print("   - Grant camera permissions to Terminal/Python")
        print("   - Try a different camera index (1, 2, etc.)")
        return False
    
    print(" Camera opened successfully!")
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f" Camera properties:")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    
    print("\n🔴 Starting video feed... Press 'q' to quit")
    
    frame_count = 0
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print(" Error: Can't receive frame")
            break
        
        frame_count += 1
        
        # Add some text overlay to show it's working
        cv2.putText(frame, f"Sentio-AI Camera Test", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Sentio-AI Camera Test', frame)
        
        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✅ Camera test completed! Processed {frame_count} frames")
    return True

def test_multiple_cameras():
    """Test if multiple cameras are available"""
    print("\n🔍 Scanning for available cameras...")
    
    available_cameras = []
    
    # Test camera indices 0-4
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    
    if available_cameras:
        print(f"✅ Found cameras at indices: {available_cameras}")
    else:
        print("❌ No cameras found")
    
    return available_cameras

if __name__ == "__main__":
    print(" Sentio-AI Camera Test Starting...")
    print("=" * 50)
    
    try:
        # Test for available cameras first
        cameras = test_multiple_cameras()
        
        if not cameras:
            print("\n❌ No cameras detected. Please check your setup.")
            sys.exit(1)
        
        # Test the main camera
        success = test_camera()
        
        if success:
            print("\n🎉 All tests passed! Your camera is ready for Sentio-AI")
        else:
            print("\n⚠️  Camera test failed. Check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Make sure OpenCV is installed: pip install opencv-python")
        sys.exit(1)
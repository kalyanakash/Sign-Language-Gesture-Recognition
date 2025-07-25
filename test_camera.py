"""
Quick Camera Test Script
Run this to test if your camera works locally before running the full app
"""

import cv2
import sys

def test_camera():
    print("🎥 Testing camera access...")
    
    try:
        # Try to access camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Camera not found or accessible")
            print("💡 Possible solutions:")
            print("   - Check if another app is using the camera")
            print("   - Try a different camera index (1, 2, etc.)")
            print("   - Make sure camera drivers are installed")
            return False
        
        print("✅ Camera found!")
        
        # Try to read a frame
        ret, frame = cap.read()
        if ret:
            print("✅ Camera is working!")
            print("📷 Frame size:", frame.shape)
            
            # Show camera feed for 3 seconds
            print("📺 Showing camera feed for 3 seconds...")
            import time
            start_time = time.time()
            
            while time.time() - start_time < 3:
                ret, frame = cap.read()
                if ret:
                    cv2.putText(frame, 'Camera Test - Working!', (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, 'Press ESC to close', (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.imshow('Camera Test', frame)
                    
                    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                        break
            
            cv2.destroyAllWindows()
            print("✅ Camera test completed successfully!")
            
        else:
            print("❌ Could not read from camera")
            return False
            
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🤟 Sign Language Detector - Camera Test")
    print("=" * 50)
    
    if test_camera():
        print("\n🎯 GREAT! Your camera is working.")
        print("📱 Now you can run the full app:")
        print("   python app.py")
        print("   Then open: http://localhost:5000")
    else:
        print("\n❌ Camera test failed.")
        print("🔧 Please fix camera issues before running the main app.")
    
    print("\n" + "=" * 50)

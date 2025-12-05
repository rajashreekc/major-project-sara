import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from main import MainWindow

def test_application():
    """Test the application with a sample image"""
    print("Testing Vitamin Deficiency Detection Application...")
    
    # Find a test image
    test_dirs = ["TA", "TB", "TC", "TD"]
    test_image = None
    
    for dir_name in test_dirs:
        dir_path = os.path.join("Testing", dir_name)
        if os.path.exists(dir_path):
            for ext in ('*.jpg', '*.png'):
                images = list(Path(dir_path).glob(ext))
                if images:
                    test_image = str(images[0])
                    break
        if test_image:
            break
    
    if not test_image:
        print("ERROR: No test images found!")
        return False
    
    print(f"Found test image: {test_image}")
    
    # Test the detector directly
    try:
        from main import VitaminDeficiencyDetector
        detector = VitaminDeficiencyDetector()
        results = detector.analyze_image(test_image)
        
        if 'error' in results:
            print(f"ERROR: {results['error']}")
            return False
        elif 'message' in results:
            print(f"RESULT: {results['message']}")
        else:
            print(f"SUCCESS: Found {len(results)} potential deficiencies")
            for result in results:
                print(f"  - {result['vitamin']}: {result['confidence']*100:.1f}% confidence")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Vitamin Deficiency Detection System Test")
    print("=" * 50)
    
    # Test 1: Check if all required files exist
    required_files = [
        "main.py",
        "utils/reference_data.py",
        "requirements.txt"
    ]
    
    print("\n1. Checking required files...")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            return False
    
    # Test 2: Check if test images exist
    print("\n2. Checking test images...")
    test_dirs = ["TA", "TB", "TC", "TD"]
    found_images = 0
    
    for dir_name in test_dirs:
        dir_path = os.path.join("Testing", dir_name)
        if os.path.exists(dir_path):
            for ext in ('*.jpg', '*.png'):
                images = list(Path(dir_path).glob(ext))
                found_images += len(images)
    
    if found_images > 0:
        print(f"✓ Found {found_images} test images")
    else:
        print("✗ No test images found")
        return False
    
    # Test 3: Test the detector
    print("\n3. Testing image analysis...")
    if test_application():
        print("✓ Image analysis test passed")
    else:
        print("✗ Image analysis test failed")
        return False
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("The application should work correctly.")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nSome tests failed. Please check the issues above.")
        sys.exit(1)

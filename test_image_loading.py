import cv2
import numpy as np
from PIL import Image
import os
from pathlib import Path

def test_image_loading():
    """Test image loading with different methods"""
    print("Testing image loading functionality...")
    
    # Test with a sample image from the Testing directory
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
    
    print(f"Testing with image: {test_image}")
    
    # Test 1: Check if file exists
    if not os.path.exists(test_image):
        print(f"ERROR: File does not exist: {test_image}")
        return False
    else:
        print("✓ File exists")
    
    # Test 2: Try loading with PIL
    try:
        pil_image = Image.open(test_image)
        print(f"✓ PIL loaded successfully: {pil_image.size}")
    except Exception as e:
        print(f"✗ PIL failed: {e}")
        return False
    
    # Test 3: Try loading with OpenCV
    try:
        cv_image = cv2.imread(test_image)
        if cv_image is None:
            print("✗ OpenCV failed to load image")
            return False
        else:
            print(f"✓ OpenCV loaded successfully: {cv_image.shape}")
    except Exception as e:
        print(f"✗ OpenCV failed: {e}")
        return False
    
    # Test 4: Try color conversion
    try:
        img_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        print(f"✓ Color conversions successful")
        print(f"  RGB shape: {img_rgb.shape}")
        print(f"  HSV shape: {img_hsv.shape}")
        print(f"  Gray shape: {gray.shape}")
    except Exception as e:
        print(f"✗ Color conversion failed: {e}")
        return False
    
    # Test 5: Try feature extraction
    try:
        # Color features
        color_features = {
            'mean_color': np.mean(img_rgb, axis=(0, 1)),
            'std_color': np.std(img_rgb, axis=(0, 1)),
            'mean_hsv': np.mean(img_hsv, axis=(0, 1)),
            'std_hsv': np.std(img_hsv, axis=(0, 1))
        }
        print(f"✓ Color features extracted: {color_features['mean_color']}")
        
        # Texture features
        texture_features = {
            'variance': np.var(gray),
            'std_dev': np.std(gray)
        }
        print(f"✓ Texture features extracted: variance={texture_features['variance']:.2f}")
        
        # Edge features
        edges = cv2.Canny(gray, 50, 150, 3)
        edge_features = {
            'edge_density': np.mean(edges > 0),
            'edge_intensity': np.mean(edges)
        }
        print(f"✓ Edge features extracted: density={edge_features['edge_density']:.4f}")
        
    except Exception as e:
        print(f"✗ Feature extraction failed: {e}")
        return False
    
    print("✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_image_loading()
    if success:
        print("\nImage loading functionality is working correctly.")
    else:
        print("\nThere are issues with image loading functionality.")

import os
from pathlib import Path
from main import VitaminDeficiencyDetector
import requests
import tempfile

def analyze_single_image(image_path, is_temp=False):
    """Analyze a single image and provide detailed output."""
    try:
        detector = VitaminDeficiencyDetector()
        
        print("\n" + "="*50)
        print(f"ANALYZING IMAGE: {Path(image_path).name}")
        print("="*50)
        
        results = detector.analyze_image(image_path)
        
        if isinstance(results, dict) and "error" in results:
            print(f"\nError: {results['error']}")
            return
        
        if isinstance(results, dict) and "message" in results:
            print(f"\n{results['message']}")
            return
            
        print("\nDETECTED DEFICIENCIES:")
        print("-" * 30)
        
        # Sort results by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        for result in results:
            print(f"\n{result['vitamin']}:")
            print(f"Confidence Level: {result['confidence']:.1%}")
            print("\nTop Symptoms:")
            for symptom in result['symptoms'][:3]:
                print(f"- {symptom}")
            
            print("\nKey Risk Factors:")
            for factor in result['risk_factors'][:3]:
                print(f"- {factor}")
            
            print("\nRecommendations:")
            for rec in result['recommendations'][:3]:
                print(f"- {rec}")
            print("-" * 30)
    
    finally:
        if is_temp and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except:
                pass

def list_test_images():
    """List all available test images."""
    test_dirs = ["TA", "TB", "TC", "TD"]
    available_images = []
    
    for dir_name in test_dirs:
        dir_path = os.path.join("Testing", dir_name)
        if os.path.exists(dir_path):
            print(f"\nImages in Testing/{dir_name}/:")
            print("-" * 30)
            
            # Get all jpg and png files (excluding copies)
            images = []
            for ext in ('*.jpg', '*.png'):
                images.extend([f for f in Path(dir_path).glob(ext) if "Copy" not in f.name])
            
            # Sort and display images
            images.sort()
            for idx, img_path in enumerate(images, 1):
                print(f"{idx}. {img_path.name}")
                available_images.append(str(img_path))
    
    return available_images

def download_from_url(url):
    """Download image from URL."""
    try:
        print("\nDownloading image...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_file.name, None
        
    except Exception as e:
        return None, f"Error downloading image: {str(e)}"

def main():
    print("Welcome to Vitamin Deficiency Detection System")
    print("=" * 45)
    
    while True:
        print("\nOptions:")
        print("1. Analyze test image")
        print("2. Analyze image from URL")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            available_images = list_test_images()
            if available_images:
                while True:
                    try:
                        img_num = input("\nEnter the number of the image to analyze (0 to go back): ")
                        if img_num == '0':
                            break
                        img_idx = int(img_num) - 1
                        if 0 <= img_idx < len(available_images):
                            analyze_single_image(available_images[img_idx])
                            break
                        else:
                            print("Invalid image number. Please try again.")
                    except ValueError:
                        print("Please enter a valid number.")
        
        elif choice == '2':
            url = input("\nEnter the image URL: ").strip()
            if url:
                temp_path, error = download_from_url(url)
                if error:
                    print(f"Error: {error}")
                else:
                    analyze_single_image(temp_path, is_temp=True)
            else:
                print("No URL provided.")
        
        elif choice == '3':
            print("\nThank you for using Vitamin Deficiency Detection System!")
            break
        
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 
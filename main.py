
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QScrollArea, QTextEdit, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PIL import Image
import os
from pathlib import Path
from utils.reference_data import VITAMIN_DEFICIENCIES, ANALYSIS_PARAMETERS, DIETARY_RECOMMENDATIONS

class VitaminDeficiencyDetector:
    def __init__(self):
        self.deficiency_data = VITAMIN_DEFICIENCIES
        self.analysis_params = ANALYSIS_PARAMETERS
        self.recommendations = DIETARY_RECOMMENDATIONS

    def analyze_image(self, image_path):
        """Analyze the image for vitamin deficiency symptoms."""
        # Check if file exists
        if not os.path.exists(image_path):
            return {"error": f"File does not exist: {image_path}"}
        
        # Read and preprocess image
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Failed to load image"}
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Extract features
        features = self._extract_features(img_rgb, img_hsv)
        
        # Analyze features for each vitamin deficiency
        results = []
        for vitamin, characteristics in self.deficiency_data.items():
            confidence = self._calculate_confidence(features, characteristics)
            if confidence > self.analysis_params['confidence_threshold']:
                results.append({
                    'vitamin': vitamin,
                    'confidence': confidence,
                    'symptoms': characteristics['symptoms'],
                    'description': characteristics['description'].strip(),
                    'risk_factors': characteristics['risk_factors'],
                    'recommendations': self.recommendations[vitamin]
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results if results else {"message": "No significant vitamin deficiencies detected"}

    def _extract_features(self, img_rgb, img_hsv):
        """Extract color and texture features from the image."""
        # Color features
        color_features = {
            'mean_color': np.mean(img_rgb, axis=(0, 1)),
            'std_color': np.std(img_rgb, axis=(0, 1)),
            'mean_hsv': np.mean(img_hsv, axis=(0, 1)),
            'std_hsv': np.std(img_hsv, axis=(0, 1))
        }
        
        # Texture features
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # Calculate texture features using block analysis
        block_size = self.analysis_params['texture_analysis']['block_size']
        texture_features = {
            'variance': np.var(gray),
            'std_dev': np.std(gray),
            'blocks': self._analyze_texture_blocks(gray, block_size)
        }
        
        # Edge features
        edges = cv2.Canny(gray, 
                         self.analysis_params['edge_detection']['low_threshold'],
                         self.analysis_params['edge_detection']['high_threshold'],
                         self.analysis_params['edge_detection']['aperture_size'])
        
        edge_features = {
            'edge_density': np.mean(edges > 0),
            'edge_intensity': np.mean(edges)
        }
        
        return {
            'color': color_features,
            'texture': texture_features,
            'edges': edge_features
        }

    def _analyze_texture_blocks(self, gray_img, block_size):
        """Analyze texture in image blocks."""
        height, width = gray_img.shape
        blocks = []
        
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                block = gray_img[y:min(y+block_size, height), 
                               x:min(x+block_size, width)]
                blocks.append({
                    'variance': np.var(block),
                    'std_dev': np.std(block)
                })
        
        return blocks

    def _calculate_confidence(self, features, characteristics):
        """Calculate confidence score for a vitamin deficiency."""
        confidence = 0.0
        
        # Color analysis
        color_conf = self._analyze_color_match(features['color'], 
                                             characteristics['color_ranges'])
        confidence += self.analysis_params['color_weight'] * color_conf
        
        # Texture analysis
        texture_conf = self._analyze_texture_match(features['texture'], 
                                                 characteristics['texture_patterns'])
        confidence += self.analysis_params['texture_weight'] * texture_conf
        
        # Edge analysis
        if features['edges']['edge_density'] >= characteristics['texture_patterns']['edge_density_min']:
            confidence *= 1.2  # Boost confidence if edge pattern matches
        
        return min(confidence, 1.0)  # Cap confidence at 1.0

    def _analyze_color_match(self, color_features, target_ranges):
        """Analyze how well the color features match the target ranges."""
        if 'skin' not in target_ranges:
            return 0.0
        
        rgb_match = self._check_color_range(color_features['mean_color'],
                                          target_ranges['skin']['rgb'])
        
        hsv_match = self._check_color_range(color_features['mean_hsv'],
                                          target_ranges['skin']['hsv'])
        
        return (rgb_match + hsv_match) / 2

    def _check_color_range(self, color, target_range):
        """Check if a color falls within a target range."""
        min_vals, max_vals = target_range
        in_range = all(min_val <= val <= max_val 
                      for val, (min_val, max_val) 
                      in zip(color, zip(min_vals, max_vals)))
        return 0.8 if in_range else 0.2

    def _analyze_texture_match(self, texture_features, pattern_info):
        """Analyze how well the texture features match the target pattern."""
        variance = texture_features['variance']
        threshold = pattern_info['rough_threshold']
        
        # Check if the texture pattern matches the expected type
        if pattern_info['pattern_type'] == 'rough':
            return 0.8 if variance > threshold else 0.2
        else:  # smooth
            return 0.8 if variance < threshold else 0.2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.detector = VitaminDeficiencyDetector()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Vitamin Deficiency Detection System')
        self.setGeometry(100, 100, 1400, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # Left panel for image display
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(600)

        # Image display
        self.image_label = QLabel()
        self.image_label.setMinimumSize(500, 500)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.image_label)

        # Upload button
        upload_btn = QPushButton('Upload Image')
        upload_btn.clicked.connect(self.upload_image)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_layout.addWidget(upload_btn)

        # Status label
        self.status_label = QLabel('Ready to analyze images')
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(self.status_label)

        # Right panel for results
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Results display
        results_label = QLabel('Analysis Results:')
        results_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        right_layout.addWidget(results_label)

        # Create a scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        
        # Results text widget
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        scroll.setWidget(self.results_text)
        right_layout.addWidget(scroll)

        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
        """)

    def upload_image(self):
        """Enhanced image upload with better error handling"""
        try:
            # Set up file dialog with better options
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif)")
            dialog.setViewMode(QFileDialog.Detail)
            
            # Set initial directory to current working directory
            current_dir = os.getcwd()
            dialog.setDirectory(current_dir)
            
            if dialog.exec_():
                file_paths = dialog.selectedFiles()
                if file_paths:
                    file_name = file_paths[0]
                    self.process_image(file_name)
                else:
                    self.status_label.setText('No file selected')
            else:
                self.status_label.setText('File dialog cancelled')
                
        except Exception as e:
            error_msg = f"Error opening file dialog: {str(e)}"
            self.status_label.setText(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def process_image(self, file_name):
        """Process the selected image with comprehensive error handling"""
        try:
            self.status_label.setText(f"Processing: {os.path.basename(file_name)}")
            
            # Check if file exists
            if not os.path.exists(file_name):
                raise FileNotFoundError(f"File does not exist: {file_name}")
            
            # Check file size
            file_size = os.path.getsize(file_name)
            if file_size == 0:
                raise ValueError("File is empty")
            
            # Try to load image with PIL first for validation
            try:
                with Image.open(file_name) as pil_image:
                    # Convert to RGB if necessary
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    print(f"PIL validation successful: {pil_image.size}")
            except Exception as e:
                raise ValueError(f"Invalid image file: {str(e)}")
            
            # Display image
            try:
                image = QImage(file_name)
                if image.isNull():
                    raise ValueError("Failed to load image with QImage")
                
                # Scale image for display
                scaled_image = image.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(QPixmap.fromImage(scaled_image))
                print(f"Image displayed successfully: {image.size()}")
                
            except Exception as e:
                raise ValueError(f"Failed to display image: {str(e)}")
            
            # Analyze image
            self.status_label.setText("Analyzing image...")
            results = self.detector.analyze_image(file_name)
            
            # Display results
            self.display_results(results)
            self.status_label.setText("Analysis completed")
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            self.status_label.setText(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
            print(f"Error: {error_msg}")

    def display_results(self, results):
        """Display analysis results"""
        if 'error' in results:
            self.results_text.setText(f"Error: {results['error']}")
        elif 'message' in results:
            self.results_text.setText(results['message'])
        else:
            results_text = "<style>"\
                         "h2 { color: #2c3e50; }"\
                         ".confidence { color: #27ae60; font-weight: bold; }"\
                         ".section { margin: 10px 0; }"\
                         ".divider { border-top: 1px solid #eee; margin: 15px 0; }"\
                         "</style>"
            
            for result in results:
                results_text += f"<h2>Vitamin Deficiency: {result['vitamin']}</h2>"
                results_text += f"<div class='confidence'>Confidence: {result['confidence']*100:.1f}%</div>"
                
                results_text += f"<div class='section'><b>Description:</b><br>{result['description']}</div>"
                
                results_text += "<div class='section'><b>Possible Symptoms:</b><ul>"
                for symptom in result['symptoms']:
                    results_text += f"<li>{symptom}</li>"
                results_text += "</ul></div>"
                
                results_text += "<div class='section'><b>Risk Factors:</b><ul>"
                for factor in result['risk_factors']:
                    results_text += f"<li>{factor}</li>"
                results_text += "</ul></div>"
                
                results_text += "<div class='section'><b>Recommendations:</b><ul>"
                for rec in result['recommendations']:
                    results_text += f"<li>{rec}</li>"
                results_text += "</ul></div>"
                
                results_text += "<div class='divider'></div>"
            
            results_text += "<p><i>Note: This analysis is preliminary. Please consult with a healthcare provider for proper diagnosis.</i></p>"
            self.results_text.setHtml(results_text)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 
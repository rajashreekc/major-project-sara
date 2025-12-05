import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QScrollArea, QTextEdit, QTabWidget, QGridLayout,
                           QFrame, QProgressBar, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests
from main import VitaminDeficiencyDetector
import tempfile
import platform

# VS Code specific configuration
if platform.system() == 'Windows':
    os.environ['QT_QPA_PLATFORM'] = 'windows'

# Error handling for high DPI displays
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

ANALYSIS_PARAMETERS = {
    'color_weight': 0.6,
    'texture_weight': 0.4,
    'confidence_threshold': 0.3,  # This is the key threshold
}

class ImageAnalysisThread(QThread):
    """Thread for running image analysis in background"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        try:
            detector = VitaminDeficiencyDetector()
            results = detector.analyze_image(self.image_path)
            if isinstance(results, dict) and "error" in results:
                self.error.emit(results["error"])
            elif isinstance(results, dict) and "message" in results:
                self.error.emit(results["message"])
            else:
                self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class ResultWidget(QWidget):
    """Widget to display a single deficiency result"""
    def __init__(self, result):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: #212529;
            }
        """)
        
        layout = QVBoxLayout()
        frame = QFrame()
        frame_layout = QVBoxLayout()
        
        # Title with confidence
        title = QLabel(f"{result['vitamin']}")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        frame_layout.addWidget(title)
        
        confidence = QLabel(f"Confidence: {result['confidence']:.1%}")
        confidence.setFont(QFont('Arial', 10))
        frame_layout.addWidget(confidence)
        
        # Progress bar for confidence
        progress = QProgressBar()
        progress.setValue(int(result['confidence'] * 100))
        progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        frame_layout.addWidget(progress)
        
        # Symptoms
        symptoms_label = QLabel("Top Symptoms:")
        symptoms_label.setFont(QFont('Arial', 10, QFont.Bold))
        frame_layout.addWidget(symptoms_label)
        for symptom in result['symptoms'][:3]:
            label = QLabel(f"• {symptom}")
            frame_layout.addWidget(label)
        
        # Risk Factors
        risks_label = QLabel("\nRisk Factors:")
        risks_label.setFont(QFont('Arial', 10, QFont.Bold))
        frame_layout.addWidget(risks_label)
        for factor in result['risk_factors'][:3]:
            label = QLabel(f"• {factor}")
            frame_layout.addWidget(label)
        
        # Recommendations
        rec_label = QLabel("\nRecommendations:")
        rec_label.setFont(QFont('Arial', 10, QFont.Bold))
        frame_layout.addWidget(rec_label)
        for rec in result['recommendations'][:3]:
            label = QLabel(f"• {rec}")
            label.setWordWrap(True)
            frame_layout.addWidget(label)
        
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.setLayout(layout)

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.temp_file = None
        
    def initUI(self):
        self.setWindowTitle('Vitamin Deficiency Detection Dashboard')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # Left panel for image and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(500)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setMinimumSize(480, 480)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)
        left_layout.addWidget(self.image_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton('Load Test Image')
        self.test_btn.clicked.connect(self.load_test_image)
        button_layout.addWidget(self.test_btn)
        
        self.url_btn = QPushButton('Load from URL')
        self.url_btn.clicked.connect(self.load_from_url)
        button_layout.addWidget(self.url_btn)
        
        left_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel('Ready to analyze images')
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        layout.addWidget(left_panel)
        
        # Right panel for results
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Results area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_widget.setLayout(self.results_layout)
        scroll.setWidget(self.results_widget)
        
        right_layout.addWidget(scroll)
        layout.addWidget(right_panel)
        
        # Initialize test image list
        self.test_images = self.get_test_images()
    
    def get_test_images(self):
        """Get list of available test images"""
        test_dirs = ["TA", "TB", "TC", "TD"]
        available_images = []
        
        for dir_name in test_dirs:
            dir_path = os.path.join("Testing", dir_name)
            if os.path.exists(dir_path):
                for ext in ('*.jpg', '*.png'):
                    available_images.extend([
                        str(f) for f in Path(dir_path).glob(ext)
                        if "Copy" not in f.name
                    ])
        
        return sorted(available_images)
    
    def load_test_image(self):
        """Show dialog to select test image"""
        if not self.test_images:
            QMessageBox.warning(self, 'Warning', 'No test images found!')
            return
            
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Images (*.jpg *.jpeg *.png)")
        dialog.setDirectory("Testing")
        
        if dialog.exec_():
            image_path = dialog.selectedFiles()[0]
            self.process_image(image_path)
    
    def load_from_url(self):
        """Load and analyze image from URL"""
        url, ok = QFileDialog.getSaveFileName(
            self, 'Enter Image URL', '', 'URL (*.*)'
        )
        
        if ok and url:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Save to temp file
                if self.temp_file:
                    try:
                        os.unlink(self.temp_file)
                    except:
                        pass
                        
                temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp.write(response.content)
                temp.close()
                self.temp_file = temp.name
                
                self.process_image(self.temp_file)
                
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to load image: {str(e)}')
    
    def process_image(self, image_path):
        """Process the selected image"""
        try:
            # Display image
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                
                # Clear previous results
                for i in reversed(range(self.results_layout.count())): 
                    self.results_layout.itemAt(i).widget().setParent(None)
                
                # Start analysis
                self.status_label.setText('Analyzing image...')
                self.analysis_thread = ImageAnalysisThread(image_path)
                self.analysis_thread.finished.connect(self.show_results)
                self.analysis_thread.error.connect(self.show_error)
                self.analysis_thread.start()
            else:
                raise Exception("Failed to load image")
                
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to process image: {str(e)}')
            self.status_label.setText('Ready to analyze images')
    
    def show_results(self, results):
        """Display analysis results"""
        self.status_label.setText('Analysis complete')
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Add result widgets
        for result in results:
            widget = ResultWidget(result)
            self.results_layout.addWidget(widget)
    
    def show_error(self, error_msg):
        """Display error message"""
        self.status_label.setText('Analysis failed')
        QMessageBox.warning(self, 'Error', error_msg)
    
    def closeEvent(self, event):
        """Clean up temp file on close"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
            except:
                pass
        event.accept()

def main():
    try:
        app = QApplication(sys.argv)
        window = DashboardWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        QMessageBox.critical(None, "Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
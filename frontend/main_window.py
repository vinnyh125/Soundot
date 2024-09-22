import io
import cv2
import sys
import time
import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundot")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.capture_button = QPushButton("Capture Image")
        self.capture_button.clicked.connect(self.capture_image)
        layout.addWidget(self.capture_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_capturing = False
        self.init_camera()

    def init_camera(self):
        self.capture = cv2.VideoCapture(0)
        if self.capture.isOpened():
            self.timer.start(30)  
            self.is_capturing = True
        else:
            QMessageBox.warning(self, "Camera Error", "Failed to open camera.")

    def update_frame(self):
        if self.is_capturing:
            ret, frame = self.capture.read()
            if ret:
                self.display_image(frame)

    def display_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.image_label.setPixmap(QPixmap.fromImage(p))

    def capture_image(self):
        if not self.is_capturing:
            QMessageBox.warning(self, "Camera Error", "Camera is not capturing. Try restarting the application.")
            return

        self.is_capturing = False  
        self.timer.stop()

        ret, frame = self.capture.read()
        if ret:
            self.display_image(frame)
            
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_bytes = img_encoded.tobytes()
           
            self.upload_image(img_bytes)

            QTimer.singleShot(2000, self.resume_live_feed)
        else:
            QMessageBox.warning(self, "Capture Error", "Failed to capture image from camera.")
            self.resume_live_feed()

    def resume_live_feed(self):
        self.is_capturing = True
        self.timer.start(30)

    def upload_image(self, img_bytes):
        try:
            files = {'image': ('captured_image.jpg', img_bytes, 'image/jpeg')}
            response = requests.post('http://localhost:5001/upload', files=files)
            
            print(f"Request URL: {response.url}")
            print(f"Request Headers: {response.request.headers}")
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            print(f"Response Content: {response.text}")
            
            response.raise_for_status()
            
            if response.headers.get('content-type') == 'application/json':
                data = response.json()
                QMessageBox.information(self, "Success", f"Image uploaded successfully. Server response: {data}")
            else:
                QMessageBox.warning(self, "Unexpected Response", f"Server responded with non-JSON data: {response.text}")
        
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Connection Error", "Failed to connect to server. Is the Flask backend running?")
        
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Request Error", f"Failed to upload image: {str(e)}\nResponse content: {getattr(e.response, 'text', 'No response content')}")
        
        except ValueError as e:  # 
            QMessageBox.critical(self, "Response Error", f"Failed to parse server response: {str(e)}\nResponse content: {response.text}")

    def closeEvent(self, event):
        if self.capture is not None:
            self.capture.release()
        event.accept()

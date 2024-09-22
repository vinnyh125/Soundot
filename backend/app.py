import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import cv2
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16mb limit

def process_image(filepath):

    img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    white_pixel_count = np.sum(binary == 255)
    
    return f"Processed image. White pixel count: {white_pixel_count}"

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        result = process_image(filepath)
        
        return jsonify({'message': f'Image {filename} successfully uploaded and processed', 'result': result}), 200

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5001)
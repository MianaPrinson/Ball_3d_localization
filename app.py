# app.py
from flask import Flask, render_template, request, jsonify
import os
import base64
import datetime
import json # For saving measurement data

app = Flask(__name__)

# Directory to save captured images
UPLOAD_FOLDER = 'captured_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# File to save measurement data
MEASUREMENTS_FILE = 'measurements.json' # Using JSON for structured data
if not os.path.exists(MEASUREMENTS_FILE):
    with open(MEASUREMENTS_FILE, 'w') as f:
        json.dump([], f) # Initialize with an empty list

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MEASUREMENTS_FILE'] = MEASUREMENTS_FILE

@app.route('/')
def index():
    """
    Renders the main HTML page for webcam capture and measurement.
    """
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Receives base64 encoded image data from the frontend,
    decodes it, and saves it as a JPEG file.
    """
    try:
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'success': False, 'message': 'No image data provided.'}), 400

        image_data_b64 = data['image'].split(',')[1] # Remove "data:image/png;base64," prefix
        image_bytes = base64.b64decode(image_data_b64)

        # Generate a unique filename using timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") # Added microseconds for more uniqueness
        filename = f"captured_image_{timestamp}.jpeg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        # --- OpenCV Integration Point (Conceptual) ---
        # At this point, 'filepath' contains the saved image.
        # You could load it with OpenCV for processing:
        # import cv2
        # img = cv2.imread(filepath)
        # # Perform some OpenCV operations, e.g., grayscale
        # gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{filename}"), gray_img)
        # ---------------------------------------------

        return jsonify({'success': True, 'message': f'Image saved as {filename}', 'filename': filename}), 200

    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/save_measurement', methods=['POST'])
def save_measurement():
    """
    Receives ball center coordinates and diameter from the frontend
    and saves it to a local JSON file.
    """
    try:
        data = request.get_json()
        center_x = data.get('centerX')
        center_y = data.get('centerY')
        diameter = data.get('diameter')
        image_filename = data.get('imageFilename') # The filename of the image it relates to

        if center_x is None or center_y is None or diameter is None or image_filename is None:
            return jsonify({'success': False, 'message': 'Missing measurement data.'}), 400

        measurement_entry = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_filename': image_filename,
            'center_x': center_x,
            'center_y': center_y,
            'diameter_pixels': diameter
        }

        # Load existing measurements, append new one, and save
        with open(app.config['MEASUREMENTS_FILE'], 'r+') as f:
            file_content = f.read()
            measurements = json.loads(file_content) if file_content else []
            measurements.append(measurement_entry)
            f.seek(0) # Go to the beginning of the file
            json.dump(measurements, f, indent=4) # Save with pretty-print
            f.truncate() # Remove remaining part if new content is shorter

        return jsonify({'success': True, 'message': 'Measurement saved successfully!'}), 200

    except Exception as e:
        print(f"Error saving measurement: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# app.py
from flask import Flask, render_template, request, jsonify
import os
import base64
import datetime

app = Flask(__name__)

# Directory to save captured images
UPLOAD_FOLDER = 'captured_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    
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
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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

if __name__ == '__main__':
    # Run the Flask app in debug mode (useful for development)
    # In a production environment, you would use a WSGI server like Gunicorn or uWSGI
    app.run(debug=True, host='0.0.0.0', port=5000)
import numpy as np
import cv2 as cv
from flask import Flask, render_template, request, jsonify
import os
import base64
import datetime
import json 
from pymongo import MongoClient
from dotenv import load_dotenv

uri = "mongodb+srv://tcr22ec025:tcr22ec025@cluster0.xya5ynd.mongodb.net/?retryWrite=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

# Test the connection
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Connection failed: {e}")

K=np.array([[2.99443089e+03 ,0.00000000e+00 ,1.51490971e+03],
            [0.00000000e+00 ,2.99529407e+03 ,1.91193177e+03],
            [0.00000000e+00, 0.00000000e+00 ,1.00000000e+00]])

dist_coord=np.array([[-0.00969174 , 0.18437321 ,-0.00503057, -0.00089529 ,-0.21888757]])

app = Flask(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("No MONGO_URI set in environment variables")

client = MongoClient(MONGO_URI)
db = client["ball_data"]  
collection = db["camera_coordinates"]  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():

    try:                        
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'success': False, 'message': 'No image data provided.'}), 400
        
        image_data_b64 = data['image']
        if ',' in image_data_b64:
            image_data_b64 = image_data_b64.split(',')[1]

        return jsonify({'success': True, 'message': 'Image received (not saved).', 'filename': None}), 200

    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500



@app.route('/ball_localization', methods=["POST"])
def localization():

    def rectify_point(pixel_coord, camera_matrix, dist_coeffs):
        
        points = np.array([[pixel_coord[0], pixel_coord[1]]], dtype=np.float32)
        undistorted = cv.undistortPoints(points, camera_matrix, dist_coeffs, P=camera_matrix)
        return undistorted[0, 0]

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON payload'}), 400

        center_x = data.get('centerX')
        center_y = data.get('centerY')
        diameter = data.get('diameter')
        image_filename = data.get('imageFilename')
        

        if any(v is None for v in [center_x, center_y, diameter]):
            return jsonify({'success': False, 'message': 'Missing centerX, centerY, or diameter in payload'}), 400
        if not all(isinstance(v, (int, float)) for v in [center_x, center_y, diameter]):
            return jsonify({'success': False, 'message': 'centerX, centerY, and diameter must be numeric'}), 400
        if diameter <= 0:
            return jsonify({'success': False, 'message': 'Diameter must be positive'}), 400

        focal = (K[0, 0] + K[1, 1]) / 2
        phi = 6.46 

        scaling_factor = (phi * focal) / diameter
        k_inv = np.linalg.inv(K)
        pcoord = np.array([center_x, center_y])
        undist_pcoord = rectify_point(pcoord, K, dist_coord)
        rec_pcoord = np.append(undist_pcoord, [1]).reshape(3, 1)
        b_c = np.matmul(k_inv, rec_pcoord)
        scaled_bc = scaling_factor * b_c

        ball_x_camera = scaled_bc[0, 0]
        ball_y_camera = scaled_bc[1, 0]
        ball_z_camera = scaled_bc[2, 0]


        db_entry = {
            "type": "measurement",
            "timestamp": datetime.datetime.now().isoformat(),
            "image_filename": image_filename,
            "pixel_coordinates": [center_x, center_y],
            "diameter": diameter,
            "ball_coordinates": [ball_x_camera, ball_y_camera, ball_z_camera]
        }
        
        result = collection.insert_one(db_entry)
        saved_id = str(result.inserted_id)

        return jsonify({
            'success': True,
            'message': 'Ball localized and saved successfully',
            'ball_position_camera_coords': {
                'x': ball_x_camera,
                'y': ball_y_camera,
                'z': ball_z_camera
            },
        }), 200
      

    except Exception as e:
        print(f"Error in localization: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

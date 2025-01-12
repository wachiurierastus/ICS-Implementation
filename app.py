from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from prep_dataset import predict
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'wav'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_stage_name(stage_number):
    stage_mapping = {
        0: "Stage 1 (Mild)",
        1: "Stage 2 (Mild to Moderate)",
        2: "Stage 3 (Moderate)",
        3: "Stage 4 (Severe)"
    }
    return stage_mapping.get(stage_number, "Unknown Stage")


@app.route('/analyze', methods=['POST'])
def analyze_audio():
    try:
        # Check if audio file is present in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']
        mmse_score = int(request.form.get('mmse', 0))
        print("mmse_app:",mmse_score)
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Call prediction function
                dementia,stage = predict(mmse_score)

                # Clean up
                os.remove(filepath)

                return jsonify({
                    'diagnosis': dementia,
                    'stage': stage
                })

            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
                return jsonify({'error': 'Prediction failed'}), 500

        return jsonify({'error': 'Invalid file type'}), 400

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
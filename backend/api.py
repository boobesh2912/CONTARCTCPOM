"""
MediGuardian Flask API - REST API layer for React frontend
Wraps existing backend functions from app.py, db_utils.py, auth_routes.py
"""
import os
import sys
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')
UPLOAD_DIR = os.path.join(TEMP_DIR, 'uploads')

# Import existing backend functions
from app import predict_parkinsons, analyze_audio_file
from db_utils import (
    initialize_database,
    authenticate_user,
    register_user,
    add_emergency_contact,
    get_user_emergency_contacts,
    save_test_result,
    get_user_test_history as get_user_tests
)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mediguardian-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}

# Enable CORS for React frontend (dev ports can vary: 3000/5173/5174/etc.)
CORS(
    app,
    origins=[r"http://localhost:\d+", r"http://127.0.0.1:\d+"],
    supports_credentials=True
)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize database
initialize_database()

# JWT token settings
JWT_SECRET = app.config['SECRET_KEY']
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_token(user_data):
    """Create JWT token for authenticated user"""
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'email': user_data['email'],
        'first_name': user_data['first_name'],
        'last_name': user_data['last_name'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to protect routes requiring authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401

        try:
            payload = decode_token(token)
            if payload is None:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            request.current_user = payload
        except Exception as e:
            return jsonify({'error': 'Token validation failed'}), 401

        return f(*args, **kwargs)

    return decorated


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        # Call existing register_user function
        success, result = register_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            dob=data.get('dob'),
            phone=data.get('phone'),
            address=data.get('address')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Call existing authenticate_user function
        success, result = authenticate_user(username, password)

        if success:
            user_data = result
            token = create_token(user_data)

            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'phone_number': user_data.get('phone_number'),
                    'date_of_birth': user_data.get('date_of_birth')
                }
            }), 200
        else:
            return jsonify({'error': result}), 401

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify JWT token is valid"""
    return jsonify({
        'success': True,
        'user': request.current_user
    }), 200


# ============================================================================
# VOICE ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """Analyze uploaded audio file for Parkinson's detection"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: WAV, MP3, OGG, FLAC, M4A'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Call existing predict_parkinsons function
        result_html = predict_parkinsons(filepath)

        # Extract data for JSON response
        # Parse features from analyze_audio_file
        y, sr, features = analyze_audio_file(filepath)

        # Determine prediction from features
        import joblib
        import numpy as np
        import pandas as pd

        model = joblib.load(os.path.join(MODELS_DIR, 'parkinson_model.pkl'))

        # Load feature names if available
        feature_names = []
        feature_names_path = os.path.join(MODELS_DIR, 'feature_names.txt')
        if os.path.exists(feature_names_path):
            with open(feature_names_path, 'r') as f:
                feature_names = f.read().splitlines()

        if feature_names:
            feature_values = [features.get(name, 0) for name in feature_names]
            feature_array = np.array([feature_values])
        else:
            features_df = pd.DataFrame([features])
            for col in ['filename', 'label']:
                if col in features_df.columns:
                    features_df = features_df.drop(col, axis=1)
            feature_array = features_df.values

        # Get prediction and confidence
        prediction = 'healthy'
        confidence = 0.5
        risk_score = 15  # Default low risk

        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(feature_array)[0]
            parkinsons_prob = probability[1] if len(probability) > 1 else 0.5
            prediction = 'parkinsons' if parkinsons_prob > 0.7 else 'healthy'
            confidence = parkinsons_prob if prediction == 'parkinsons' else (1 - parkinsons_prob)
            risk_score = int(parkinsons_prob * 100)
        else:
            prediction = model.predict(feature_array)[0]
            confidence = 0.8

        # Generate recommendations
        recommendations = []
        if prediction == 'healthy':
            recommendations = [
                'Your voice patterns show normal characteristics',
                'Continue monitoring with regular tests',
                'Maintain a healthy lifestyle and stay active'
            ]
        else:
            recommendations = [
                'Consult with a healthcare professional for comprehensive evaluation',
                'Consider scheduling a neurological examination',
                'Keep track of any physical symptoms (tremors, stiffness, balance issues)'
            ]

        # Save test result if user is authenticated
        user_id = None
        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split(' ')[1]
                payload = decode_token(token)
                if payload:
                    user_id = payload['user_id']
                    save_test_result(
                        user_id=user_id,
                        test_type='parkinsons_voice',
                        prediction=prediction,
                        confidence=confidence,
                        features=features,
                        audio_path=filepath
                    )
            except:
                pass  # Continue without saving if token invalid

        # Return JSON response
        return jsonify({
            'success': True,
            'prediction': prediction,
            'confidence': float(confidence),
            'risk_score': risk_score,
            'features': {
                'jitter_relative': float(features.get('jitter_relative', 0)),
                'shimmer_relative': float(features.get('shimmer_relative', 0)),
                'hnr': float(features.get('hnr', 0)),
                'f0_mean': float(features.get('f0_mean', 0))
            },
            'visualizations': {
                'waveform_url': f'/api/temp/waveform.png?t={timestamp}',
                'spectrogram_url': f'/api/temp/spectrogram.png?t={timestamp}'
            },
            'recommendations': recommendations,
            'audio_file': filename
        }), 200

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    """Get user dashboard data including test history"""
    try:
        user_id = request.current_user['user_id']

        # Get test history
        success, test_results = get_user_tests(user_id)

        if not success:
            return jsonify({'error': 'Failed to retrieve test history'}), 500

        # Format test history for frontend
        test_history = []
        for test in test_results:
            test_history.append({
                'id': test['id'],
                'date': test['test_date'],
                'prediction': test['prediction'],
                'confidence': float(test['confidence']),
                'risk_score': int(float(test['confidence']) * 100) if test['prediction'] == 'parkinsons' else int((1 - float(test['confidence'])) * 100),
                'test_type': test['test_type']
            })

        # Calculate statistics
        total_tests = len(test_history)
        avg_confidence = sum(t['confidence'] for t in test_history) / total_tests if total_tests > 0 else 0
        latest_risk = test_history[0]['risk_score'] if test_history else 0

        return jsonify({
            'success': True,
            'user': request.current_user,
            'statistics': {
                'total_tests': total_tests,
                'avg_confidence': round(avg_confidence * 100, 1),
                'latest_risk_score': latest_risk
            },
            'test_history': test_history
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve dashboard: {str(e)}'}), 500


@app.route('/api/results/<test_id>', methods=['GET'])
@token_required
def get_test_result(test_id):
    """Get detailed results for a specific test"""
    try:
        user_id = request.current_user['user_id']

        # Get all tests and find the specific one
        success, test_results = get_user_tests(user_id)

        if not success:
            return jsonify({'error': 'Failed to retrieve test result'}), 500

        # Find specific test
        test = next((t for t in test_results if t['id'] == test_id), None)

        if not test:
            return jsonify({'error': 'Test not found'}), 404

        # Parse features string to dict
        import ast
        features = ast.literal_eval(test['features'])

        return jsonify({
            'success': True,
            'test': {
                'id': test['id'],
                'date': test['test_date'],
                'prediction': test['prediction'],
                'confidence': float(test['confidence']),
                'features': features,
                'audio_file': test.get('audio_file_path')
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve test result: {str(e)}'}), 500


# ============================================================================
# PROFILE & EMERGENCY CONTACTS
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile information"""
    return jsonify({
        'success': True,
        'user': request.current_user
    }), 200


@app.route('/api/profile/emergency', methods=['POST'])
@token_required
def add_emergency():
    """Add emergency contact for user"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']

        required_fields = ['name', 'relationship', 'phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        success, result = add_emergency_contact(
            user_id=user_id,
            name=data['name'],
            relationship=data['relationship'],
            phone=data['phone'],
            email=data.get('email'),
            is_primary=data.get('is_primary', False)
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Emergency contact added',
                'contact_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to add emergency contact: {str(e)}'}), 500


@app.route('/api/profile/emergency', methods=['GET'])
@token_required
def get_emergency_contacts():
    """Get all emergency contacts for user"""
    try:
        user_id = request.current_user['user_id']

        success, contacts = get_user_emergency_contacts(user_id)

        if not success:
            return jsonify({'error': 'Failed to retrieve emergency contacts'}), 500

        return jsonify({
            'success': True,
            'contacts': contacts
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve emergency contacts: {str(e)}'}), 500


# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/api/temp/<filename>', methods=['GET'])
def serve_temp_file(filename):
    """Serve temporary files (waveforms, spectrograms)"""
    try:
        return send_from_directory(TEMP_DIR, filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/uploads/<filename>', methods=['GET'])
@token_required
def serve_upload_file(filename):
    """Serve uploaded audio files (requires authentication)"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MediGuardian API',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'MediGuardian API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'verify': 'GET /api/auth/verify'
            },
            'analysis': {
                'analyze': 'POST /api/analyze'
            },
            'dashboard': {
                'dashboard': 'GET /api/dashboard',
                'result': 'GET /api/results/<test_id>'
            },
            'profile': {
                'profile': 'GET /api/profile',
                'add_emergency': 'POST /api/profile/emergency',
                'get_emergency': 'GET /api/profile/emergency'
            }
        }
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'

    print("=" * 70)
    print("MediGuardian API Server Starting...")
    print("=" * 70)
    print("API running at: http://localhost:5000")
    print("API docs at: http://localhost:5000/")
    print("CORS enabled for localhost dev ports")
    print("=" * 70)

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode,
        threaded=True
    )

"""
MediGuardian Flask API - REST API layer for React frontend
Wraps existing backend functions from app.py, db_utils.py, auth_routes.py
"""
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import joblib
import numpy as np
import pandas as pd
import librosa
from librosa import display as librosa_display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')
UPLOAD_DIR = os.path.join(TEMP_DIR, 'uploads')

# Import existing backend functions
from db_utils import (
    initialize_database,
    get_db_connection,
    authenticate_user,
    register_user,
    add_emergency_contact,
    get_user_emergency_contacts,
    save_test_result,
    get_user_test_history as get_user_tests,
    # Doctor booking system functions
    add_doctor,
    get_all_doctors,
    get_doctor_by_id,
    add_doctor_availability,
    get_doctor_availability,
    create_appointment,
    get_user_appointments,
    get_doctor_appointments,
    update_appointment_status,
    add_doctor_review,
    get_doctor_reviews
)
from multi_disease_detector import analyze_multi_disease, get_recording_instructions
from utils.advanced_features import extract_advanced_features

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
PARKINSON_MODEL: Optional[Any] = None
PARKINSON_FEATURE_NAMES: List[str] = []
READINESS_TABLES = ['users', 'test_results', 'doctors', 'doctor_availability', 'appointments', 'doctor_reviews']


def initialize_model_cache() -> None:
    """Load reusable model assets once at process startup."""
    global PARKINSON_MODEL, PARKINSON_FEATURE_NAMES

    model_path = os.path.join(MODELS_DIR, 'parkinson_model.pkl')
    feature_names_path = os.path.join(MODELS_DIR, 'feature_names.txt')

    if os.path.exists(model_path):
        PARKINSON_MODEL = joblib.load(model_path)
        print(f"Loaded Parkinson model from {model_path}")
    else:
        print(f"Warning: model file not found at {model_path}")

    if os.path.exists(feature_names_path):
        with open(feature_names_path, 'r') as f:
            PARKINSON_FEATURE_NAMES = f.read().splitlines()
        print(f"Loaded {len(PARKINSON_FEATURE_NAMES)} feature names from {feature_names_path}")
    else:
        PARKINSON_FEATURE_NAMES = []
        print(f"Warning: feature names file not found at {feature_names_path}")


if os.environ.get('MEDIGUARDIAN_EAGER_MODEL_LOAD', '0') == '1':
    initialize_model_cache()


def collect_readiness() -> Dict[str, Any]:
    """Collect runtime readiness diagnostics for production monitoring."""
    readiness: Dict[str, Any] = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'model_cache': {
            'parkinson_model_loaded': PARKINSON_MODEL is not None,
            'feature_name_count': len(PARKINSON_FEATURE_NAMES),
        },
        'database': {
            'connected': False,
            'missing_tables': [],
            'doctor_count': 0,
        },
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        readiness['database']['connected'] = True

        missing_tables: List[str] = []
        for table in READINESS_TABLES:
            cursor.execute(
                "SELECT COUNT(*) as c FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if cursor.fetchone()['c'] == 0:
                missing_tables.append(table)

        readiness['database']['missing_tables'] = missing_tables

        if 'doctors' not in missing_tables:
            cursor.execute("SELECT COUNT(*) as c FROM doctors")
            readiness['database']['doctor_count'] = int(cursor.fetchone()['c'])

        conn.close()
    except Exception as exc:
        readiness['database']['error'] = str(exc)

    model_ready = readiness['model_cache']['parkinson_model_loaded']
    db_ready = readiness['database']['connected'] and len(readiness['database']['missing_tables']) == 0
    seeded = readiness['database']['doctor_count'] > 0
    readiness['status'] = 'ready' if (model_ready and db_ready and seeded) else 'degraded'

    return readiness


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def analyze_audio_file(audio_file: str):
    """Process audio and generate feature set + temporary visualizations."""
    y, sr = librosa.load(audio_file)

    os.makedirs(TEMP_DIR, exist_ok=True)

    plt.figure(figsize=(12, 4))
    plt.plot(np.linspace(0, len(y) / sr, len(y)), y)
    plt.title('Audio Waveform')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.savefig(os.path.join(TEMP_DIR, 'waveform.png'))
    plt.close()

    plt.figure(figsize=(12, 6))
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    librosa_display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.tight_layout()
    plt.savefig(os.path.join(TEMP_DIR, 'spectrogram.png'))
    plt.close()

    features = extract_advanced_features(y, sr)
    return y, sr, features


def create_token(user_data: Dict[str, Any]) -> str:
    """Create JWT token for authenticated user"""
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'email': user_data['email'],
        'first_name': user_data['first_name'],
        'last_name': user_data['last_name'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
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

        # Extract data for JSON response
        # Parse features from analyze_audio_file
        y, sr, features = analyze_audio_file(filepath)

        if PARKINSON_MODEL is None:
            initialize_model_cache()
        if PARKINSON_MODEL is None:
            return jsonify({'error': 'Prediction model is not available on server'}), 503

        # Load feature names if available
        if PARKINSON_FEATURE_NAMES:
            feature_values = [features.get(name, 0) for name in PARKINSON_FEATURE_NAMES]
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

        if hasattr(PARKINSON_MODEL, 'predict_proba'):
            probability = PARKINSON_MODEL.predict_proba(feature_array)[0]
            parkinsons_prob = probability[1] if len(probability) > 1 else 0.5
            prediction = 'parkinsons' if parkinsons_prob > 0.7 else 'healthy'
            confidence = parkinsons_prob if prediction == 'parkinsons' else (1 - parkinsons_prob)
            risk_score = int(parkinsons_prob * 100)
        else:
            prediction = PARKINSON_MODEL.predict(feature_array)[0]
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


@app.route('/api/analyze/multi-disease', methods=['POST'])
def analyze_audio_multi_disease():
    """Analyze uploaded audio file for multiple neurological disorders"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: WAV, MP3, OGG, FLAC, M4A'}), 400

        # Get test type from form data
        test_type = request.form.get('test_type', 'sustained_vowel')

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Perform multi-disease analysis
        results = analyze_multi_disease(filepath, test_type=test_type)

        # Save test result if user is authenticated
        user_id = None
        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split(' ')[1]
                payload = decode_token(token)
                if payload:
                    user_id = payload['user_id']

                    # Save with primary disease info
                    primary = results['primary_diagnosis']
                    save_test_result(
                        user_id=user_id,
                        test_type=f'multi_disease_{test_type}',
                        prediction=primary['disease'],
                        confidence=primary['probability'] / 100,
                        features=results['key_features'],
                        audio_path=filepath
                    )
            except:
                pass  # Continue without saving if token invalid

        # Generate visualizations (using existing function)
        y, sr, _ = analyze_audio_file(filepath)

        # Add visualization URLs
        results['visualizations'] = {
            'waveform_url': f'/api/temp/waveform.png?t={timestamp}',
            'spectrogram_url': f'/api/temp/spectrogram.png?t={timestamp}'
        }
        results['audio_file'] = filename

        return jsonify(results), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/recording-instructions/<test_type>', methods=['GET'])
def get_instructions(test_type):
    """Get recording instructions for specific test type"""
    try:
        instructions = get_recording_instructions(test_type)
        return jsonify({
            'success': True,
            'instructions': instructions
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get instructions: {str(e)}'}), 500


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
# DOCTOR BOOKING SYSTEM ENDPOINTS
# ============================================================================

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get all available doctors with optional filters"""
    try:
        city = request.args.get('city')
        specialization = request.args.get('specialization')

        success, doctors = get_all_doctors(city=city, specialization=specialization)

        if not success:
            return jsonify({'error': 'Failed to retrieve doctors'}), 500

        return jsonify({
            'success': True,
            'doctors': doctors,
            'count': len(doctors)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve doctors: {str(e)}'}), 500


@app.route('/api/doctors/<doctor_id>', methods=['GET'])
def get_doctor_details(doctor_id):
    """Get detailed information about a specific doctor"""
    try:
        success, doctor = get_doctor_by_id(doctor_id)

        if not success:
            return jsonify({'error': doctor}), 404

        # Get doctor's availability
        success_avail, availability = get_doctor_availability(doctor_id)
        if success_avail:
            doctor['availability'] = availability

        # Get doctor's reviews
        success_reviews, reviews = get_doctor_reviews(doctor_id)
        if success_reviews:
            doctor['reviews'] = reviews

        return jsonify({
            'success': True,
            'doctor': doctor
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve doctor details: {str(e)}'}), 500


@app.route('/api/doctors', methods=['POST'])
@token_required
def add_new_doctor():
    """Add a new doctor (admin only in production - add role check)"""
    try:
        data = request.get_json()

        required_fields = ['full_name', 'email', 'phone_number', 'specialization',
                          'qualification', 'experience_years', 'city', 'state',
                          'consultation_fee']

        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        success, result = add_doctor(
            full_name=data['full_name'],
            email=data['email'],
            phone_number=data['phone_number'],
            specialization=data['specialization'],
            qualification=data['qualification'],
            experience_years=data['experience_years'],
            city=data['city'],
            state=data['state'],
            consultation_fee=data['consultation_fee'],
            sub_specialties=data.get('sub_specialties'),
            hospital_affiliation=data.get('hospital_affiliation'),
            clinic_address=data.get('clinic_address'),
            about=data.get('about'),
            languages=data.get('languages')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Doctor added successfully',
                'doctor_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to add doctor: {str(e)}'}), 500


@app.route('/api/appointments', methods=['POST'])
@token_required
def book_appointment():
    """Book an appointment with a doctor"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']

        required_fields = ['doctor_id', 'appointment_date', 'appointment_time']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        success, result = create_appointment(
            user_id=user_id,
            doctor_id=data['doctor_id'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            test_result_id=data.get('test_result_id'),
            symptoms=data.get('symptoms'),
            notes=data.get('notes'),
            risk_score=data.get('risk_score')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Appointment booked successfully',
                'appointment_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to book appointment: {str(e)}'}), 500


@app.route('/api/appointments', methods=['GET'])
@token_required
def get_appointments():
    """Get all appointments for the authenticated user"""
    try:
        user_id = request.current_user['user_id']
        status = request.args.get('status')

        success, appointments = get_user_appointments(user_id, status=status)

        if not success:
            return jsonify({'error': 'Failed to retrieve appointments'}), 500

        return jsonify({
            'success': True,
            'appointments': appointments,
            'count': len(appointments)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve appointments: {str(e)}'}), 500


@app.route('/api/appointments/<appointment_id>', methods=['PATCH'])
@token_required
def update_appointment(appointment_id):
    """Update appointment status (cancel, reschedule, etc.)"""
    try:
        data = request.get_json()

        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400

        success, result = update_appointment_status(
            appointment_id=appointment_id,
            status=data['status'],
            cancellation_reason=data.get('cancellation_reason')
        )

        if success:
            return jsonify({
                'success': True,
                'message': result
            }), 200
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to update appointment: {str(e)}'}), 500


@app.route('/api/doctors/<doctor_id>/reviews', methods=['POST'])
@token_required
def add_review(doctor_id):
    """Add a review for a doctor"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']

        if 'rating' not in data:
            return jsonify({'error': 'Rating is required'}), 400

        if not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        success, result = add_doctor_review(
            doctor_id=doctor_id,
            user_id=user_id,
            rating=data['rating'],
            review_text=data.get('review_text'),
            appointment_id=data.get('appointment_id')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Review added successfully',
                'review_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to add review: {str(e)}'}), 500


@app.route('/api/doctors/<doctor_id>/reviews', methods=['GET'])
def get_reviews(doctor_id):
    """Get all reviews for a doctor"""
    try:
        success, reviews = get_doctor_reviews(doctor_id)

        if not success:
            return jsonify({'error': 'Failed to retrieve reviews'}), 500

        return jsonify({
            'success': True,
            'reviews': reviews,
            'count': len(reviews)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve reviews: {str(e)}'}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    readiness = collect_readiness()

    return jsonify({
        'status': 'healthy' if readiness['status'] == 'ready' else 'degraded',
        'service': 'MediGuardian API',
        'version': '1.0.0',
        'readiness': {
            'status': readiness['status'],
            'model_cached': readiness['model_cache']['parkinson_model_loaded'],
            'database_connected': readiness['database']['connected'],
            'missing_tables': readiness['database']['missing_tables'],
            'doctor_count': readiness['database']['doctor_count'],
        }
    }), 200


@app.route('/api/health/readiness', methods=['GET'])
def readiness_check():
    """Detailed readiness endpoint for deployment checks."""
    readiness = collect_readiness()
    status_code = 200 if readiness['status'] == 'ready' else 503
    return jsonify(readiness), status_code


@app.route('/api/seed-status', methods=['GET'])
def seed_status():
    """Return doctor-seed status to verify booking bootstrap."""
    readiness = collect_readiness()
    return jsonify({
        'success': True,
        'doctor_count': readiness['database']['doctor_count'],
        'seeded': readiness['database']['doctor_count'] > 0,
        'missing_tables': readiness['database']['missing_tables'],
        'status': readiness['status'],
        'checked_at': readiness['checked_at'],
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
                'analyze': 'POST /api/analyze',
                'analyze_multi_disease': 'POST /api/analyze/multi-disease',
                'recording_instructions': 'GET /api/recording-instructions/<test_type>'
            },
            'health': {
                'liveness': 'GET /api/health',
                'readiness': 'GET /api/health/readiness',
                'seed_status': 'GET /api/seed-status'
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

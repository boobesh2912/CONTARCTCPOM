#!/usr/bin/env python3
"""
MediGuardian End-to-End Test Suite
Tests the Flask API endpoints without needing to start the server
"""

import sys
import os
import json
import tempfile
import wave
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print(" MediGuardian - End-to-End Application Test")
print("=" * 70)
print()

# Test counters
tests_passed = 0
tests_failed = 0

def test_result(name, passed, message=""):
    """Print test result"""
    global tests_passed, tests_failed
    if passed:
        print(f"[PASS] {name}")
        tests_passed += 1
    else:
        print(f"[FAIL] {name}")
        if message:
            print(f"   Error: {message}")
        tests_failed += 1

# ============================================================================
# TEST 1: Check Required Files
# ============================================================================
print("[1] Checking Required Files...")
print("-" * 70)

required_files = [
    'app.py',
    'db_utils.py',
    'auth_routes.py',
    'utils/advanced_features.py',
    'models/parkinson_model.pkl',
    'models/feature_names.txt',
    'backend/api.py',
    'backend/requirements.txt',
    'frontend/package.json',
    'frontend/src/App.jsx',
    'frontend/src/api.js',
]

for file_path in required_files:
    exists = os.path.exists(file_path)
    test_result(f"File exists: {file_path}", exists)

print()

# ============================================================================
# TEST 2: Import Core Modules
# ============================================================================
print("[2] Testing Core Module Imports...")
print("-" * 70)

try:
    from app import predict_parkinsons, analyze_audio_file
    test_result("Import app.py functions", True)
except Exception as e:
    test_result("Import app.py functions", False, str(e))

try:
    from db_utils import (
        initialize_database, authenticate_user, register_user,
        save_test_result, get_user_test_history
    )
    test_result("Import db_utils.py functions", True)
except Exception as e:
    test_result("Import db_utils.py functions", False, str(e))

try:
    from utils.advanced_features import extract_advanced_features
    test_result("Import advanced_features.py", True)
except Exception as e:
    test_result("Import advanced_features.py", False, str(e))

print()

# ============================================================================
# TEST 3: Database Initialization
# ============================================================================
print("[3] Testing Database Operations...")
print("-" * 70)

try:
    initialize_database()
    test_result("Database initialization", True)
except Exception as e:
    test_result("Database initialization", False, str(e))

# Test user registration
try:
    test_username = f"testuser_{np.random.randint(1000, 9999)}"
    success, user_id = register_user(
        username=test_username,
        password="testpassword123",
        email=f"{test_username}@test.com",
        first_name="Test",
        last_name="User"
    )
    test_result("User registration", success, user_id if not success else "")

    if success:
        # Test user authentication
        auth_success, user_data = authenticate_user(test_username, "testpassword123")
        test_result("User authentication (correct password)", auth_success)

        # Test wrong password
        auth_fail, _ = authenticate_user(test_username, "wrongpassword")
        test_result("User authentication (wrong password rejected)", not auth_fail)

except Exception as e:
    test_result("User registration/authentication", False, str(e))

print()

# ============================================================================
# TEST 4: Audio Feature Extraction
# ============================================================================
print("[4] Testing Audio Processing...")
print("-" * 70)

# Create a simple test audio file
try:
    # Generate a simple sine wave (440 Hz, 2 seconds)
    sample_rate = 22050
    duration = 2.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_audio_path = temp_file.name

        with wave.open(temp_audio_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    test_result("Generate test audio file", True)

    # Test feature extraction
    try:
        import librosa
        y, sr = librosa.load(temp_audio_path)
        features = extract_advanced_features(y, sr)

        # Check that features were extracted
        required_features = ['jitter_relative', 'shimmer_relative', 'hnr', 'f0_mean']
        all_present = all(f in features for f in required_features)

        test_result("Extract audio features", all_present)

        if all_present:
            print(f"   Sample features: jitter={features['jitter_relative']:.4f}, "
                  f"shimmer={features['shimmer_relative']:.4f}, "
                  f"HNR={features['hnr']:.2f}")

    except Exception as e:
        test_result("Extract audio features", False, str(e))

    # Test full prediction pipeline
    try:
        result = predict_parkinsons(temp_audio_path)
        has_result = isinstance(result, str) and len(result) > 0
        test_result("Full prediction pipeline", has_result)

        if has_result:
            # Check if result contains expected elements
            has_prediction = 'healthy' in result.lower() or 'parkinsons' in result.lower()
            has_confidence = 'confidence' in result.lower()
            test_result("Prediction contains required data", has_prediction and has_confidence)

    except Exception as e:
        test_result("Full prediction pipeline", False, str(e))

    # Clean up temp file
    os.unlink(temp_audio_path)

except Exception as e:
    test_result("Audio processing test setup", False, str(e))

print()

# ============================================================================
# TEST 5: Flask API Module Check
# ============================================================================
print("[5] Testing Flask API Module...")
print("-" * 70)

try:
    sys.path.insert(0, 'backend')
    from api import app, create_token, decode_token
    test_result("Import Flask API", True)

    # Test token generation
    try:
        test_user = {
            'id': 'test123',
            'username': 'testuser',
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        token = create_token(test_user)
        test_result("Generate JWT token", isinstance(token, str) and len(token) > 0)

        # Test token decoding
        decoded = decode_token(token)
        matches = decoded['username'] == test_user['username']
        test_result("Decode and validate JWT token", matches)

    except Exception as e:
        test_result("JWT token operations", False, str(e))

except Exception as e:
    test_result("Import Flask API", False, str(e))

print()

# ============================================================================
# TEST 6: Frontend Files Check
# ============================================================================
print("[6] Testing Frontend Files...")
print("-" * 70)

frontend_files = {
    'frontend/package.json': ['react', 'axios', 'react-router-dom'],
    'frontend/src/api.js': ['authAPI', 'analysisAPI', 'dashboardAPI'],
    'frontend/src/App.jsx': ['BrowserRouter', 'Routes', 'Route'],
}

for file_path, required_strings in frontend_files.items():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            all_present = all(s in content for s in required_strings)
            test_result(f"Frontend file has required content: {file_path}", all_present)
    except Exception as e:
        test_result(f"Read frontend file: {file_path}", False, str(e))

# Check React components
components = [
    'Landing.jsx',
    'Login.jsx',
    'Register.jsx',
    'Dashboard.jsx',
    'TestPage.jsx',
    'Profile.jsx'
]

for component in components:
    component_path = f'frontend/src/components/{component}'
    exists = os.path.exists(component_path)
    test_result(f"React component exists: {component}", exists)

print()

# ============================================================================
# TEST 7: Configuration Files
# ============================================================================
print("[7] Testing Configuration Files...")
print("-" * 70)

# Check backend requirements.txt
try:
    with open('backend/requirements.txt', 'r') as f:
        requirements = f.read()
        required_packages = ['flask', 'flask-cors', 'pyjwt', 'librosa', 'scikit-learn']
        all_present = all(pkg in requirements.lower() for pkg in required_packages)
        test_result("Backend requirements.txt has required packages", all_present)
except Exception as e:
    test_result("Read backend requirements.txt", False, str(e))

# Check frontend package.json
try:
    with open('frontend/package.json', 'r') as f:
        package_json = json.load(f)
        required_deps = ['react', 'axios', 'react-router-dom']
        all_present = all(dep in package_json.get('dependencies', {}) for dep in required_deps)
        test_result("Frontend package.json has required dependencies", all_present)
except Exception as e:
    test_result("Read frontend package.json", False, str(e))

# Check Vite config
vite_exists = os.path.exists('frontend/vite.config.js')
test_result("Vite config exists", vite_exists)

# Check Tailwind config
tailwind_exists = os.path.exists('frontend/tailwind.config.js')
test_result("Tailwind config exists", tailwind_exists)

print()

# ============================================================================
# TEST 8: Documentation
# ============================================================================
print("[8] Testing Documentation...")
print("-" * 70)

docs = [
    'README_FLASK_REACT.md',
    'SETUP_GUIDE.md',
    'MIGRATION_SUMMARY.md',
    'ARCHITECTURE.md'
]

for doc in docs:
    exists = os.path.exists(doc)
    test_result(f"Documentation exists: {doc}", exists)

print()

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("=" * 70)
print(" TEST RESULTS SUMMARY")
print("=" * 70)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
print("=" * 70)

if tests_failed == 0:
    print()
    print("ALL TESTS PASSED! Your application is ready to run!")
    print()
    print("Next steps:")
    print("1. Start the backend:  cd backend && python api.py")
    print("2. Start the frontend: cd frontend && npm run dev")
    print("3. Open browser:       http://localhost:3000")
    print()
else:
    print()
    print("Some tests failed. Please review the errors above.")
    print()

sys.exit(0 if tests_failed == 0 else 1)

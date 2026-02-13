# 🏗️ MediGuardian Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React Frontend (Port 3000)                   │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  Landing   │  │   Login    │  │  Register  │         │  │
│  │  │  Page      │  │   Page     │  │   Page     │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │ Dashboard  │  │  TestPage  │  │  Profile   │         │  │
│  │  │            │  │  (Record)  │  │            │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────┐         │  │
│  │  │         api.js (Axios HTTP Client)          │         │  │
│  │  │  - authAPI.login()                          │         │  │
│  │  │  - analysisAPI.analyzeAudio()               │         │  │
│  │  │  - dashboardAPI.getDashboard()              │         │  │
│  │  │  - profileAPI.getProfile()                  │         │  │
│  │  └─────────────────────────────────────────────┘         │  │
│  └───────────────────────────┬─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                      HTTP/JSON (JWT Token)
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                    Flask API Server (Port 5000)                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    backend/api.py                         │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐     │  │
│  │  │           API Endpoints (Flask Routes)          │     │  │
│  │  │                                                  │     │  │
│  │  │  POST /api/auth/register                        │     │  │
│  │  │  POST /api/auth/login   → JWT Token             │     │  │
│  │  │  POST /api/analyze      → ML Prediction         │     │  │
│  │  │  GET  /api/dashboard    → Test History          │     │  │
│  │  │  GET  /api/profile      → User Info             │     │  │
│  │  │  POST /api/profile/emergency                    │     │  │
│  │  └─────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐     │  │
│  │  │        Authentication Middleware                 │     │  │
│  │  │  - JWT Token Validation                          │     │  │
│  │  │  - @token_required Decorator                     │     │  │
│  │  └─────────────────────────────────────────────────┘     │  │
│  └───────────────────────────┬─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                      Python Function Calls
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│              Existing Backend Modules (UNCHANGED)               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                        app.py                             │  │
│  │                                                           │  │
│  │  def predict_parkinsons(audio_path):                      │  │
│  │      # Load model                                         │  │
│  │      model = joblib.load('models/parkinson_model.pkl')   │  │
│  │      # Extract features                                   │  │
│  │      y, sr, features = analyze_audio_file(audio_path)    │  │
│  │      # Make prediction                                    │  │
│  │      prediction = model.predict_proba(feature_array)     │  │
│  │      return result                                        │  │
│  │                                                           │  │
│  │  def analyze_audio_file(audio_path):                      │  │
│  │      # Load audio with librosa                            │  │
│  │      y, sr = librosa.load(audio_path)                    │  │
│  │      # Generate waveform image                            │  │
│  │      plt.savefig('temp/waveform.png')                    │  │
│  │      # Generate spectrogram image                         │  │
│  │      plt.savefig('temp/spectrogram.png')                 │  │
│  │      # Extract features                                   │  │
│  │      features = extract_advanced_features(y, sr)         │  │
│  │      return y, sr, features                               │  │
│  └───────────────────────────┬─────────────────────────────┘  │
│                               │                                 │
│  ┌────────────────────────────▼─────────────────────────────┐  │
│  │           utils/advanced_features.py                      │  │
│  │                                                           │  │
│  │  def extract_advanced_features(audio, sr):                │  │
│  │      # Extract MFCC, jitter, shimmer, HNR, F0, etc.      │  │
│  │      features['jitter_relative'] = ...                   │  │
│  │      features['shimmer_relative'] = ...                  │  │
│  │      features['hnr'] = ...                               │  │
│  │      return features                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      db_utils.py                          │  │
│  │                                                           │  │
│  │  def authenticate_user(username, password):               │  │
│  │      # Hash password and compare with database           │  │
│  │      return success, user_data                            │  │
│  │                                                           │  │
│  │  def register_user(username, password, email, ...):       │  │
│  │      # Create new user in database                        │  │
│  │      return success, user_id                              │  │
│  │                                                           │  │
│  │  def save_test_result(user_id, prediction, ...):          │  │
│  │      # Save test result to database                       │  │
│  │      return success, result_id                            │  │
│  │                                                           │  │
│  │  def get_user_test_history(user_id):                      │  │
│  │      # Retrieve all tests for user                        │  │
│  │      return success, test_results                         │  │
│  └───────────────────────────┬─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                          SQL Queries
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     SQLite Database                             │
│                                                                 │
│  database/mediguardian.db                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tables:                                                  │  │
│  │  - users                                                  │  │
│  │  - test_results                                           │  │
│  │  - emergency_contacts                                     │  │
│  │  - medical_history                                        │  │
│  │  - doctor_referrals                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Machine Learning Model                     │
│                                                                 │
│  models/parkinson_model.pkl (Trained Classifier)                │
│  models/feature_names.txt (Feature List)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Temporary Files Storage                     │
│                                                                 │
│  temp/                                                          │
│  ├── waveform.png      (Generated by matplotlib)               │
│  ├── spectrogram.png   (Generated by librosa)                  │
│  └── uploads/          (Uploaded audio files)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow Example: Voice Test

```
1. User clicks "Start Recording" in TestPage.jsx
   │
   ├─▶ MediaRecorder API captures audio from microphone
   │
2. User clicks "Stop Recording"
   │
   ├─▶ Frontend creates audio Blob and File object
   │
3. User clicks "Analyze Audio"
   │
   ├─▶ TestPage.jsx calls: analysisAPI.analyzeAudio(audioFile)
   │
   ├─▶ api.js sends: POST /api/analyze
   │      Headers: Authorization: Bearer <JWT_TOKEN>
   │      Body: multipart/form-data with audio file
   │
4. Flask API receives request
   │
   ├─▶ @token_required decorator validates JWT token
   │
   ├─▶ Saves file to temp/uploads/
   │
   ├─▶ Calls: predict_parkinsons(filepath)  [from app.py]
   │      │
   │      ├─▶ Calls: analyze_audio_file(filepath)  [from app.py]
   │      │      │
   │      │      ├─▶ librosa.load() loads audio
   │      │      ├─▶ matplotlib generates waveform → temp/waveform.png
   │      │      ├─▶ librosa generates spectrogram → temp/spectrogram.png
   │      │      ├─▶ Calls: extract_advanced_features(y, sr)
   │      │      │      [from utils/advanced_features.py]
   │      │      │      └─▶ Returns: {jitter, shimmer, hnr, f0, mfccs, ...}
   │      │      │
   │      │      └─▶ Returns: y, sr, features
   │      │
   │      ├─▶ Loads: models/parkinson_model.pkl
   │      ├─▶ model.predict_proba(feature_array)
   │      ├─▶ Determines: prediction, confidence, risk_score
   │      └─▶ Returns: HTML result (converted to JSON by Flask)
   │
   ├─▶ Flask formats response as JSON:
   │      {
   │        prediction: "healthy" / "parkinsons",
   │        confidence: 0.87,
   │        risk_score: 15,
   │        features: {jitter, shimmer, hnr, f0},
   │        visualizations: {
   │          waveform_url: "/api/temp/waveform.png",
   │          spectrogram_url: "/api/temp/spectrogram.png"
   │        }
   │      }
   │
   ├─▶ If authenticated, calls: save_test_result()  [from db_utils.py]
   │      └─▶ Inserts test result into SQLite database
   │
5. Frontend receives JSON response
   │
   ├─▶ TestPage.jsx updates state: setResult(response.data)
   │
   ├─▶ Displays risk score, confidence bar
   │
   ├─▶ Renders waveform image: <img src={getImageUrl(waveform_url)} />
   │      └─▶ Browser requests: GET /api/temp/waveform.png
   │             └─▶ Flask serves file from temp/ directory
   │
   └─▶ User sees complete results
```

## Data Flow: User Dashboard

```
1. User navigates to /dashboard
   │
   ├─▶ React Router renders Dashboard.jsx
   │
2. useEffect() runs on mount
   │
   ├─▶ Calls: dashboardAPI.getDashboard()
   │
   ├─▶ api.js sends: GET /api/dashboard
   │      Headers: Authorization: Bearer <JWT_TOKEN>
   │
3. Flask API receives request
   │
   ├─▶ @token_required validates JWT
   │
   ├─▶ Extracts user_id from JWT payload
   │
   ├─▶ Calls: get_user_test_history(user_id)  [from db_utils.py]
   │      │
   │      ├─▶ Queries SQLite: SELECT * FROM test_results WHERE user_id = ?
   │      │
   │      └─▶ Returns: list of test result dictionaries
   │
   ├─▶ Calculates statistics:
   │      - total_tests
   │      - avg_confidence
   │      - latest_risk_score
   │
   ├─▶ Returns JSON:
   │      {
   │        statistics: {...},
   │        test_history: [
   │          {id, date, prediction, confidence, risk_score},
   │          ...
   │        ]
   │      }
   │
4. Frontend receives JSON
   │
   ├─▶ Dashboard.jsx updates state: setDashboardData(response.data)
   │
   ├─▶ Renders stats cards
   │
   ├─▶ Generates trend chart from test_history
   │
   └─▶ Displays recent tests list
```

## Authentication Flow

```
Registration:
User fills form → POST /api/auth/register → register_user() → SQLite INSERT → Success

Login:
User submits credentials → POST /api/auth/login → authenticate_user()
  → Check password hash → Generate JWT → Return token → Store in localStorage

Protected Route:
React checks localStorage → Has token? → Include in Authorization header
  → Flask validates JWT → Allow request / Return 401

Logout:
User clicks logout → Frontend removes token from localStorage → Redirect to login
```

## Technology Stack

```
Frontend:
├── React 18 (UI Library)
├── React Router 6 (Routing)
├── Axios (HTTP Client)
├── Tailwind CSS (Styling)
├── Vite (Build Tool)
└── Lucide React (Icons)

Backend:
├── Flask 3.0 (Web Framework)
├── Flask-CORS (Cross-Origin Resource Sharing)
├── PyJWT (JWT Token Generation)
├── Werkzeug (WSGI Utilities)
├── Librosa (Audio Processing)
├── Scikit-learn (Machine Learning)
├── Matplotlib (Visualization)
└── SQLite3 (Database)
```

## File Structure by Layer

```
Presentation Layer (Frontend):
  frontend/src/components/*.jsx

API Layer (Backend):
  backend/api.py

Business Logic Layer (ML & Processing):
  app.py
  utils/advanced_features.py

Data Access Layer (Database):
  db_utils.py
  auth_routes.py

Data Storage Layer:
  database/mediguardian.db
  models/parkinson_model.pkl
  temp/uploads/*.wav
  temp/*.png
```

---

This architecture ensures:
- ✅ **Separation of Concerns** - Frontend, API, Business Logic, Database are separate
- ✅ **Reusability** - Existing ML code is reused without modification
- ✅ **Scalability** - Frontend and Backend can scale independently
- ✅ **Maintainability** - Clear structure makes updates easier
- ✅ **Security** - JWT authentication, CORS protection, input validation

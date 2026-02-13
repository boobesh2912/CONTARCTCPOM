# MediGuardian - Flask + React Architecture

This document explains how to run the new Flask API backend with React frontend.

## 🏗️ Architecture Overview

```
MediGuardian/
├── backend/
│   ├── api.py              # NEW: Flask REST API (main server)
│   └── requirements.txt    # Flask + existing dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api.js          # Axios API client
│   │   ├── App.jsx         # Main app + routing
│   │   └── main.jsx        # Entry point
│   ├── package.json
│   └── index.html
├── app.py                  # Existing ML functions (imported by api.py)
├── db_utils.py            # Existing database functions
├── auth_routes.py         # Existing auth functions
└── utils/
    └── advanced_features.py  # Existing feature extraction
```

## 🚀 Quick Start

### Step 1: Backend Setup (Flask API)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create/activate virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Flask API:**
   ```bash
   python api.py
   ```

   The API will start at: **http://localhost:5000**

   You should see:
   ```
   🚀 MediGuardian API Server Starting...
   📡 API running at: http://localhost:5000
   ```

### Step 2: Frontend Setup (React)

1. **Open a NEW terminal and navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start React development server:**
   ```bash
   npm run dev
   ```

   The frontend will start at: **http://localhost:3000**

   Open your browser and go to: **http://localhost:3000**

## 📋 Available API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/verify` - Verify token validity

### Analysis
- `POST /api/analyze` - Upload audio file for Parkinson's detection
  - Accepts: multipart/form-data with 'audio' file
  - Returns: prediction, confidence, risk_score, features, visualizations

### Dashboard
- `GET /api/dashboard` - Get user dashboard with test history
- `GET /api/results/<test_id>` - Get specific test details

### Profile
- `GET /api/profile` - Get user profile
- `POST /api/profile/emergency` - Add emergency contact
- `GET /api/profile/emergency` - Get all emergency contacts

### Static Files
- `GET /api/temp/<filename>` - Serve waveform/spectrogram images
- `GET /api/uploads/<filename>` - Serve audio files (authenticated)

## 🔧 How It Works

### Data Flow

1. **User visits frontend** (React app at localhost:3000)
2. **User logs in** → Frontend sends credentials to `/api/auth/login`
3. **Backend authenticates** → Calls `authenticate_user()` from db_utils.py
4. **Returns JWT token** → Frontend stores in localStorage
5. **User records audio** → Frontend captures via MediaRecorder API
6. **Uploads audio** → POST to `/api/analyze` with JWT token
7. **Backend processes** → Calls `predict_parkinsons()` from app.py
8. **ML prediction** → Uses existing librosa + sklearn model
9. **Returns results** → JSON with prediction, confidence, visualizations
10. **Frontend displays** → Shows waveform, spectrogram, risk score

### Authentication Flow

```
Frontend (React)
    ↓ POST /api/auth/login {username, password}
Flask API (api.py)
    ↓ calls authenticate_user()
Database (db_utils.py)
    ↓ returns user data
Flask API
    ↓ generates JWT token
Frontend
    ↓ stores token in localStorage
    ↓ includes in Authorization header for future requests
Protected Endpoints
```

## 🛠️ Key Features

### ✅ What's Been Preserved
- ✅ All existing ML functions from `app.py`
- ✅ `predict_parkinsons()` - unchanged
- ✅ `analyze_audio_file()` - unchanged
- ✅ All database functions from `db_utils.py`
- ✅ Feature extraction from `advanced_features.py`
- ✅ SQLite database schema - unchanged
- ✅ Model loading from `parkinson_model.pkl`
- ✅ Waveform & spectrogram generation

### 🆕 What's New
- 🆕 Flask REST API layer (`backend/api.py`)
- 🆕 JWT authentication
- 🆕 CORS support for React frontend
- 🆕 JSON response format (instead of HTML)
- 🆕 Modern React frontend with Vite
- 🆕 React Router for navigation
- 🆕 Axios for API calls
- 🆕 Tailwind CSS styling
- 🆕 Real-time audio recording

## 📝 Development Notes

### Backend (Flask)

The Flask API (`backend/api.py`) is a thin wrapper around your existing functions:

```python
# Example: How the login endpoint works
@app.route('/api/auth/login', methods=['POST'])
def login():
    # Get credentials from request
    username = request.json.get('username')
    password = request.json.get('password')

    # Call existing function from db_utils.py
    success, result = authenticate_user(username, password)

    if success:
        # Generate JWT token
        token = create_token(result)
        return jsonify({'token': token, 'user': result})
    else:
        return jsonify({'error': result}), 401
```

### Frontend (React)

The React app uses modern hooks and routing:

```javascript
// Example: How login works
import { authAPI } from '../api';

const handleLogin = async () => {
  const response = await authAPI.login({username, password});
  localStorage.setItem('token', response.data.token);
  navigate('/dashboard');
};
```

### Audio Recording

The TestPage component uses the MediaRecorder API:

```javascript
// Record audio from microphone
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);

// Or upload existing file
<input type="file" accept="audio/*" onChange={handleFileUpload} />
```

## 🐛 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'flask'`
**Solution:** Make sure you're in the virtual environment and ran `pip install -r requirements.txt`

**Problem:** `FileNotFoundError: models/parkinson_model.pkl`
**Solution:** Make sure you've run `train_model.py` to generate the model file

**Problem:** CORS errors in browser console
**Solution:** Check that Flask-CORS is installed and api.py has `CORS(app, origins=['http://localhost:3000'])`

### Frontend Issues

**Problem:** `npm: command not found`
**Solution:** Install Node.js from https://nodejs.org/ (LTS version)

**Problem:** `Cannot GET /api/analyze`
**Solution:** Make sure Flask backend is running on port 5000

**Problem:** Authentication errors
**Solution:** Clear localStorage in browser DevTools → Application → Local Storage

### Database Issues

**Problem:** `no such table: users`
**Solution:** The database is auto-initialized on first run. If issues persist, delete `database/mediguardian.db` and restart the backend.

## 🎯 Testing the Application

### Test User Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### Test Audio Analysis
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@path/to/audio.wav"
```

## 📦 Production Deployment

### Backend
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

### Frontend
```bash
# Build for production
cd frontend
npm run build

# Serve the dist/ folder with Nginx or similar
```

### Environment Variables
Create a `.env` file in backend/:
```
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
```

## 🔐 Security Notes

- JWT secret key should be changed in production (set `SECRET_KEY` environment variable)
- CORS origins should be restricted to your production domain
- Consider adding rate limiting to prevent abuse
- Use HTTPS in production
- Validate and sanitize all user inputs

## 📊 Feature Comparison

| Feature | Gradio Version | Flask+React Version |
|---------|----------------|---------------------|
| UI Framework | Gradio (Python) | React (JavaScript) |
| Styling | Built-in | Tailwind CSS (customizable) |
| Backend | Gradio server | Flask REST API |
| Auth | Session-based | JWT tokens |
| Mobile | Limited | Fully responsive |
| Customization | Limited | Full control |
| API Access | No | Yes (REST API) |

## 🆘 Need Help?

- Check the Flask logs in the backend terminal
- Check the browser console (F12) for frontend errors
- Look at Network tab in DevTools to see API requests/responses
- Verify both servers are running (backend on 5000, frontend on 3000)

## 📚 Next Steps

1. ✅ Test all features (registration, login, audio analysis, dashboard)
2. 🎨 Customize the UI colors and branding
3. 📊 Add more visualizations to the dashboard
4. 🔔 Implement email notifications for high-risk results
5. 📄 Add PDF export functionality
6. 🌍 Deploy to production (AWS, Heroku, etc.)

---

**Happy Coding! 🚀**

# 🚀 MediGuardian - Complete Setup Guide

## 📁 Project Structure

```
MediGuardian/
│
├── 🔧 BACKEND FILES (Keep these - they work!)
│   ├── app.py                          # ML prediction functions
│   ├── db_utils.py                     # Database operations
│   ├── auth_routes.py                  # Authentication helpers
│   ├── utils/
│   │   └── advanced_features.py        # Audio feature extraction
│   ├── models/
│   │   ├── parkinson_model.pkl         # Trained ML model
│   │   └── feature_names.txt           # Feature list
│   └── database/
│       └── mediguardian.db             # SQLite database
│
├── 🆕 NEW BACKEND (Flask API)
│   └── backend/
│       ├── api.py                      # ⭐ NEW: Flask REST API
│       └── requirements.txt            # Flask dependencies
│
├── 🆕 NEW FRONTEND (React)
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── Landing.jsx         # Landing page
│       │   │   ├── Login.jsx           # Login page
│       │   │   ├── Register.jsx        # Registration page
│       │   │   ├── Dashboard.jsx       # User dashboard
│       │   │   ├── TestPage.jsx        # Voice test page
│       │   │   └── Profile.jsx         # User profile
│       │   ├── api.js                  # Axios API client
│       │   ├── App.jsx                 # Main app + routing
│       │   ├── main.jsx                # Entry point
│       │   └── index.css               # Tailwind styles
│       ├── public/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       ├── tailwind.config.js
│       └── postcss.config.js
│
├── 📝 DOCUMENTATION
│   ├── README_FLASK_REACT.md           # Main documentation
│   ├── SETUP_GUIDE.md                  # This file
│   ├── START_SERVERS.bat               # Windows startup script
│   └── START_SERVERS.sh                # Linux/Mac startup script
│
└── 📦 OLD FILES (Optional - can archive)
    ├── index.html                      # Old standalone React demo
    └── dashboard.py                    # Old Gradio dashboard
```

## ⚡ Quick Start (5 Minutes)

### Option 1: Use Startup Scripts (Easiest)

**Windows:**
```bash
# Double-click START_SERVERS.bat
# OR run in terminal:
START_SERVERS.bat
```

**Mac/Linux:**
```bash
chmod +x START_SERVERS.sh
./START_SERVERS.sh
```

### Option 2: Manual Setup

#### Step 1: Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python api.py
```

#### Step 2: Frontend Setup (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

#### Step 3: Open Browser
Go to: **http://localhost:3000**

## 🎯 First-Time Setup Checklist

- [ ] **Install Python 3.8+** (https://python.org)
- [ ] **Install Node.js 18+** (https://nodejs.org)
- [ ] **Verify installations:**
  ```bash
  python --version   # Should be 3.8+
  node --version     # Should be 18+
  npm --version      # Should be 9+
  ```
- [ ] **Install backend dependencies:**
  ```bash
  cd backend
  pip install -r requirements.txt
  ```
- [ ] **Install frontend dependencies:**
  ```bash
  cd frontend
  npm install
  ```
- [ ] **Verify model exists:**
  ```bash
  # Check that models/parkinson_model.pkl exists
  # If not, run: python train_model.py
  ```
- [ ] **Start both servers** (see Quick Start above)
- [ ] **Test in browser:** http://localhost:3000

## 🧪 Test Your Setup

### 1. Test Backend API
Open terminal and run:
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "healthy", "service": "MediGuardian API", "version": "1.0.0"}
```

### 2. Test Frontend
Open browser to: **http://localhost:3000**

You should see the MediGuardian landing page.

### 3. Test Full Flow
1. Click **"Sign Up"** → Create account
2. Click **"Sign In"** → Login
3. Click **"New Test"** → Record/upload audio
4. View results with waveform and predictions

## 🔧 Common Issues & Solutions

### Issue: "Module not found: flask"
**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "npm: command not found"
**Solution:** Install Node.js from https://nodejs.org

### Issue: "Port 5000 already in use"
**Solution:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :5000
kill -9 <PID>
```

### Issue: CORS errors in browser
**Solution:** Make sure Flask backend is running on port 5000

### Issue: Database errors
**Solution:** Delete `database/mediguardian.db` and restart backend (it will recreate)

## 📊 API Endpoints Reference

### Authentication
```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/verify
```

### Analysis
```
POST /api/analyze          (multipart/form-data)
```

### Dashboard
```
GET /api/dashboard
GET /api/results/<test_id>
```

### Profile
```
GET  /api/profile
POST /api/profile/emergency
GET  /api/profile/emergency
```

## 🎨 Customization Guide

### Change Colors (Tailwind)
Edit `frontend/tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      primary: '#2563EB',  // Change this
      secondary: '#10B981'  // And this
    }
  }
}
```

### Change API Port
**Backend:** Edit `backend/api.py`:
```python
app.run(port=5000)  # Change to your port
```

**Frontend:** Edit `frontend/vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000'  // Match backend port
  }
}
```

### Add New API Endpoint
**Backend:** Edit `backend/api.py`:
```python
@app.route('/api/my-endpoint', methods=['POST'])
def my_endpoint():
    return jsonify({'message': 'Hello!'})
```

**Frontend:** Edit `frontend/src/api.js`:
```javascript
export const myAPI = {
  myEndpoint: () => api.post('/my-endpoint')
};
```

## 🚀 Deployment Checklist

### Before Deploying:
- [ ] Change JWT secret key (set `SECRET_KEY` env var)
- [ ] Update CORS origins to production domain
- [ ] Build frontend: `npm run build`
- [ ] Use production server (gunicorn) for backend
- [ ] Set up SSL/HTTPS
- [ ] Configure database backups
- [ ] Add rate limiting
- [ ] Set up monitoring/logging

### Deployment Options:
- **Backend:** Heroku, Railway, AWS EC2, DigitalOcean
- **Frontend:** Vercel, Netlify, AWS S3 + CloudFront
- **Full Stack:** AWS Elastic Beanstalk, Google Cloud Run

## 📚 Learning Resources

- **Flask:** https://flask.palletsprojects.com/
- **React:** https://react.dev/
- **Vite:** https://vitejs.dev/
- **Tailwind CSS:** https://tailwindcss.com/
- **Axios:** https://axios-http.com/

## 💡 Pro Tips

1. **Use React DevTools:** Install the browser extension for debugging
2. **Check Network Tab:** Use browser DevTools to see API requests/responses
3. **Read the Logs:** Backend errors show in the Flask terminal
4. **Hot Reload:** Both servers auto-reload when you save files
5. **Test API with curl:** Easier than using the UI for debugging

## 🆘 Getting Help

If you're stuck:
1. Check the [README_FLASK_REACT.md](README_FLASK_REACT.md) for detailed docs
2. Look at browser console (F12) for frontend errors
3. Check Flask terminal for backend errors
4. Verify both servers are running:
   - Backend: http://localhost:5000/api/health
   - Frontend: http://localhost:3000

## ✅ Success Indicators

You know everything is working when:
- ✅ Backend shows "API running at: http://localhost:5000"
- ✅ Frontend shows "Local: http://localhost:3000"
- ✅ You can register a new account
- ✅ You can login successfully
- ✅ You can record/upload audio and see predictions
- ✅ Dashboard shows your test history
- ✅ Waveform and spectrogram images display correctly

---

**🎉 Congratulations! You're ready to use MediGuardian!**

Need more help? Check out [README_FLASK_REACT.md](README_FLASK_REACT.md)

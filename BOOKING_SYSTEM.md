# MediGuardian Doctor Booking System

## Overview

The **Doctor Booking System** is a comprehensive feature that transforms MediGuardian from a diagnostic tool into a complete healthcare platform. It enables users to book consultations with specialized neurologists directly through the platform, especially when their Parkinson's disease risk score indicates the need for professional evaluation.

---

## Key Features

### 1. **Automated Risk-Based Recommendations**
- Users with **risk score ≥ 70%** see a prominent consultation alert
- Users with **risk score ≥ 50%** get a "Find a Doctor" button
- Seamless integration with the voice analysis workflow

### 2. **Doctor Directory**
- Browse neurologists by:
  - **City** (Bangalore, Mumbai, Delhi, Hyderabad, Kochi, etc.)
  - **Specialization** (Movement Disorders, Parkinson's Specialist, General Neurology)
- View detailed doctor profiles including:
  - Qualifications and experience
  - Hospital affiliation
  - Consultation fees
  - Patient ratings and reviews
  - Languages spoken
  - About section

### 3. **Appointment Booking**
- Select available doctors
- Choose appointment date and time
- Add symptoms and notes
- Automatic linking to test results (for risk score tracking)
- Real-time booking confirmation

### 4. **Appointment Management**
- View all appointments (scheduled, completed, cancelled)
- Cancel appointments with reason tracking
- Status badges for easy identification
- Test result integration (shows risk score in appointment)

### 5. **Doctor Reviews**
- Rate doctors (1-5 stars)
- Write detailed reviews
- View other patients' reviews
- Automatic doctor rating calculation

---

## Database Schema

### New Tables

#### **doctors**
Stores neurologist information
```sql
- id: TEXT PRIMARY KEY (UUID)
- full_name: TEXT NOT NULL
- email: TEXT UNIQUE NOT NULL
- phone_number: TEXT NOT NULL
- specialization: TEXT NOT NULL (Movement Disorders, Parkinson's Specialist, etc.)
- sub_specialties: TEXT (Specific areas like DBS, Gait Disorders)
- qualification: TEXT NOT NULL (MBBS, MD, DM, etc.)
- experience_years: INTEGER NOT NULL
- hospital_affiliation: TEXT
- clinic_address: TEXT
- city: TEXT NOT NULL
- state: TEXT NOT NULL
- consultation_fee: REAL NOT NULL
- about: TEXT (Doctor's bio)
- profile_image_url: TEXT
- languages: TEXT (Comma-separated)
- rating: REAL DEFAULT 0.0
- total_reviews: INTEGER DEFAULT 0
- is_available: BOOLEAN DEFAULT 1
- created_at: TEXT NOT NULL
- updated_at: TEXT
```

#### **doctor_availability**
Doctor's weekly schedule
```sql
- id: TEXT PRIMARY KEY
- doctor_id: TEXT NOT NULL (FK to doctors.id)
- day_of_week: INTEGER NOT NULL (1=Monday, 7=Sunday)
- start_time: TEXT NOT NULL (HH:MM format)
- end_time: TEXT NOT NULL (HH:MM format)
- slot_duration: INTEGER DEFAULT 30 (minutes)
- is_active: BOOLEAN DEFAULT 1
```

#### **appointments**
Booking records
```sql
- id: TEXT PRIMARY KEY
- user_id: TEXT NOT NULL (FK to users.id)
- doctor_id: TEXT NOT NULL (FK to doctors.id)
- test_result_id: TEXT (FK to test_results.id, optional)
- appointment_date: TEXT NOT NULL (YYYY-MM-DD)
- appointment_time: TEXT NOT NULL (HH:MM)
- status: TEXT NOT NULL DEFAULT 'scheduled'
  - Values: 'scheduled', 'completed', 'cancelled', 'no-show'
- booking_type: TEXT NOT NULL DEFAULT 'consultation'
- symptoms: TEXT
- notes: TEXT
- risk_score: INTEGER (from test result if linked)
- created_at: TEXT NOT NULL
- updated_at: TEXT
- cancellation_reason: TEXT
```

#### **doctor_reviews**
Patient reviews and ratings
```sql
- id: TEXT PRIMARY KEY
- doctor_id: TEXT NOT NULL (FK to doctors.id)
- user_id: TEXT NOT NULL (FK to users.id)
- appointment_id: TEXT (FK to appointments.id, optional)
- rating: INTEGER NOT NULL (1-5)
- review_text: TEXT
- created_at: TEXT NOT NULL
```

---

## API Endpoints

### Doctor Endpoints

#### `GET /api/doctors`
Get all available doctors with optional filters
- **Query Params:**
  - `city` (optional): Filter by city
  - `specialization` (optional): Filter by specialization
- **Response:**
```json
{
  "success": true,
  "doctors": [...],
  "count": 8
}
```

#### `GET /api/doctors/:doctor_id`
Get detailed information about a specific doctor
- **Response:**
```json
{
  "success": true,
  "doctor": {
    "id": "...",
    "full_name": "Rajesh Kumar",
    "specialization": "Movement Disorders Specialist",
    "availability": [...],
    "reviews": [...]
  }
}
```

#### `POST /api/doctors`
Add a new doctor (admin only - requires authentication)
- **Body:**
```json
{
  "full_name": "...",
  "email": "...",
  "phone_number": "...",
  "specialization": "...",
  "qualification": "...",
  "experience_years": 15,
  "city": "...",
  "state": "...",
  "consultation_fee": 1500.00,
  ...
}
```

### Appointment Endpoints

#### `POST /api/appointments`
Book an appointment (requires authentication)
- **Body:**
```json
{
  "doctor_id": "...",
  "appointment_date": "2026-02-20",
  "appointment_time": "10:30",
  "symptoms": "Tremors in right hand, difficulty walking",
  "notes": "Patient has family history",
  "risk_score": 75
}
```

#### `GET /api/appointments`
Get all appointments for authenticated user
- **Query Params:**
  - `status` (optional): Filter by status
- **Response:**
```json
{
  "success": true,
  "appointments": [
    {
      "id": "...",
      "doctor_name": "Rajesh Kumar",
      "specialization": "Movement Disorders Specialist",
      "appointment_date": "2026-02-20",
      "appointment_time": "10:30",
      "status": "scheduled",
      "risk_score": 75
    }
  ]
}
```

#### `PATCH /api/appointments/:appointment_id`
Update appointment status
- **Body:**
```json
{
  "status": "cancelled",
  "cancellation_reason": "User requested cancellation"
}
```

### Review Endpoints

#### `POST /api/doctors/:doctor_id/reviews`
Add a review for a doctor (requires authentication)
- **Body:**
```json
{
  "rating": 5,
  "review_text": "Excellent doctor, very thorough examination",
  "appointment_id": "..." (optional)
}
```

#### `GET /api/doctors/:doctor_id/reviews`
Get all reviews for a doctor
- **Response:**
```json
{
  "success": true,
  "reviews": [...],
  "count": 12
}
```

---

## Frontend Components

### [Bookings.jsx](frontend/src/components/Bookings.jsx)
Main booking interface with two tabs:

1. **Find Doctors Tab**
   - Search filters (city, specialization)
   - Doctor cards with profile information
   - "Book Appointment" button
   - Star rating display

2. **My Appointments Tab**
   - List of user's appointments
   - Status badges (scheduled, completed, cancelled)
   - Appointment details (date, time, doctor, risk score)
   - Cancel appointment functionality

### Booking Modal
- Date picker (future dates only)
- Time picker
- Symptoms textarea
- Notes textarea
- Confirmation button

### Risk-Based Alerts (TestPage.jsx)
- **High Risk (≥70%):** Prominent red alert with "Book Consultation Now" button
- **Moderate Risk (≥50%):** "Find a Doctor" button in recommendations section

---

## Usage Guide

### For Patients

#### 1. Taking a Voice Test
```
1. Navigate to "Voice Test" tab
2. Record or upload audio sample
3. Click "Analyze Sample"
4. Review results and risk score
5. If risk score ≥ 70%, see booking recommendation
```

#### 2. Finding a Doctor
```
1. Click "Consultations" tab in navigation
2. Use filters to search by city/specialization
3. Review doctor profiles
4. Click "Book Appointment" on desired doctor
```

#### 3. Booking an Appointment
```
1. Select appointment date (future date)
2. Select appointment time
3. Enter symptoms (optional)
4. Add notes (optional)
5. Click "Confirm Booking"
6. View confirmation and appointment details
```

#### 4. Managing Appointments
```
1. Navigate to "My Appointments" tab
2. View all scheduled/past appointments
3. Click "Cancel Appointment" if needed
4. Provide cancellation reason
```

### For Administrators

#### Adding Doctors

**Method 1: Seed Script (Recommended for initial setup)**
```bash
python seed_doctors.py
```

**Method 2: API Endpoint**
```bash
POST /api/doctors
Authorization: Bearer <admin_token>

{
  "full_name": "Doctor Name",
  "email": "doctor@example.com",
  ...
}
```

#### Adding Doctor Availability
```python
from db_utils import add_doctor_availability

# Add Monday 9 AM - 5 PM availability
add_doctor_availability(
    doctor_id="doctor-uuid",
    day_of_week=1,  # Monday
    start_time="09:00",
    end_time="17:00",
    slot_duration=30  # 30-minute slots
)
```

---

## Setup Instructions

### 1. Database Migration
The booking system tables are automatically created when you run the application. The `initialize_database()` function in `db_utils.py` now includes the new tables.

### 2. Seed Sample Doctors
```bash
cd "c:\Users\boobe\Desktop\MediGuardian (2)\MediGuardian"
python seed_doctors.py
```

This will add 8 sample neurologists across different Indian cities.

### 3. Update API Imports
Already done in [backend/api.py](backend/api.py):
```python
from db_utils import (
    ...
    add_doctor,
    get_all_doctors,
    get_doctor_by_id,
    create_appointment,
    get_user_appointments,
    ...
)
```

### 4. Frontend Routes
Already configured in [App.jsx](frontend/src/App.jsx):
```jsx
<Route path="/bookings" element={
  isAuthenticated ? <Bookings user={user} onLogout={handleLogout} />
  : <Navigate to="/login" replace />
} />
```

### 5. Start Servers
```bash
# Backend
cd backend
python api.py

# Frontend (new terminal)
cd frontend
npm run dev
```

---

## Integration with Voice Analysis

### Automatic Linking
When a user books an appointment after a voice test:
- The `test_result_id` is automatically captured
- The `risk_score` from the test is stored with the appointment
- Doctors can see the patient's risk score in their appointment list

### Risk-Based Workflow
```
Voice Test → High Risk Result (≥70%)
    ↓
Prominent Alert Shown
    ↓
User Clicks "Book Consultation Now"
    ↓
Redirected to Bookings Page
    ↓
User Selects Doctor and Books
    ↓
Appointment Created with Risk Score
    ↓
Doctor Receives Notification (future feature)
```

---

## Future Enhancements

### Phase 1 (Immediate)
- [x] Database schema
- [x] API endpoints
- [x] Frontend booking interface
- [x] Risk-based recommendations
- [x] Appointment management

### Phase 2 (Recommended)
- [ ] Email notifications for booking confirmations
- [ ] SMS reminders 24 hours before appointment
- [ ] Doctor dashboard for managing appointments
- [ ] Video consultation integration (Zoom/Google Meet)
- [ ] Payment gateway integration (Razorpay/Stripe)

### Phase 3 (Advanced)
- [ ] AI-powered doctor recommendations based on symptoms
- [ ] Appointment rescheduling
- [ ] Prescription upload/download
- [ ] Medical report sharing
- [ ] Follow-up appointment scheduling
- [ ] Doctor-patient chat system

---

## Security Considerations

### Current Implementation
✅ JWT authentication required for all booking endpoints
✅ User can only view/manage their own appointments
✅ SQL injection protection via parameterized queries
✅ Input validation on required fields

### Recommended Additions
⚠️ Add rate limiting on booking endpoints (prevent spam)
⚠️ Add CAPTCHA for public doctor search
⚠️ Implement role-based access control (admin vs patient vs doctor)
⚠️ Add booking cancellation limits (e.g., max 3 cancellations per month)
⚠️ Verify appointment time is not in the past
⚠️ Prevent double-booking same time slot

---

## Sample Doctors (Seeded Data)

| Doctor | Specialization | City | Fee | Experience |
|--------|----------------|------|-----|------------|
| Dr. Rajesh Kumar | Movement Disorders Specialist | Bangalore | ₹1500 | 15 years |
| Dr. Priya Sharma | General Neurologist | Mumbai | ₹1200 | 12 years |
| Dr. Anil Mehta | Parkinson's Disease Specialist | Delhi | ₹2000 | 18 years |
| Dr. Meena Iyer | Movement Disorders Specialist | Bangalore | ₹1300 | 10 years |
| Dr. Suresh Patel | General Neurologist | Delhi | ₹1000 | 8 years |
| Dr. Kavita Reddy | Movement Disorders Specialist | Hyderabad | ₹1800 | 20 years |
| Dr. Vikram Singh | Parkinson's Disease Specialist | Mumbai | ₹1600 | 14 years |
| Dr. Anjali Nair | General Neurologist | Kochi | ₹1100 | 9 years |

All doctors have:
- Monday-Friday availability (9 AM - 5 PM)
- 30-minute consultation slots
- Multiple language support
- Hospital affiliations

---

## Testing the Feature

### Test Scenario 1: High-Risk User Journey
```
1. Login to MediGuardian
2. Navigate to "Voice Test"
3. Upload a sample audio file
4. Wait for analysis results
5. Verify risk score shows ≥ 70%
6. Verify red alert appears: "Immediate Consultation Recommended"
7. Click "Book Consultation Now"
8. Verify redirect to Bookings page
9. Select "Dr. Rajesh Kumar" in Bangalore
10. Click "Book Appointment"
11. Fill in appointment details
12. Confirm booking
13. Verify appointment appears in "My Appointments" tab
```

### Test Scenario 2: Browse and Book
```
1. Login to MediGuardian
2. Navigate to "Consultations" tab
3. Filter by City: "Mumbai"
4. Filter by Specialization: "Parkinson's Disease Specialist"
5. Click "Search"
6. Verify "Dr. Vikram Singh" appears
7. Review profile (rating, experience, fees)
8. Click "Book Appointment"
9. Select future date and time
10. Enter symptoms: "Hand tremors, stiffness"
11. Confirm booking
12. Navigate to "My Appointments"
13. Verify appointment is listed with status "scheduled"
```

### Test Scenario 3: Cancel Appointment
```
1. Navigate to "My Appointments"
2. Find a scheduled appointment
3. Click "Cancel Appointment"
4. Confirm cancellation
5. Verify status changes to "cancelled"
```

---

## Troubleshooting

### Issue: No doctors appear in search
**Solution:** Run `python seed_doctors.py` to populate database

### Issue: Booking button disabled
**Solution:** Ensure user is authenticated and has valid JWT token

### Issue: Appointment time in the past
**Solution:** Frontend date picker has `min={new Date().toISOString().split('T')[0]}`

### Issue: Risk-based alert not showing
**Solution:** Verify test result has `risk_score >= 70` in response

---

## Performance Considerations

### Database Optimization
- Index on `doctors.city` and `doctors.specialization` for fast filtering
- Index on `appointments.user_id` for quick user query
- Index on `appointments.doctor_id` for doctor schedule lookup

### Caching Strategy (Future)
- Cache doctor list for 1 hour (Redis)
- Cache doctor availability for 30 minutes
- Invalidate cache on doctor profile update

### Scalability
- Current SQLite works for <1000 users
- Migrate to PostgreSQL for production scale
- Consider appointment queue system for high-traffic doctors

---

## Conclusion

The Doctor Booking System seamlessly integrates with MediGuardian's voice analysis platform to provide end-to-end Parkinson's disease screening and consultation. Users can:

✅ Get diagnosed via voice analysis
✅ Receive risk-based recommendations
✅ Find specialized neurologists
✅ Book appointments instantly
✅ Manage their healthcare journey

This transforms MediGuardian into a **complete healthcare platform** rather than just a diagnostic tool.

---

**For questions or support, contact the development team.**

import sqlite3
import os
import hashlib
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(PROJECT_ROOT, 'database')
DB_PATH = os.path.join(DB_DIR, 'mediguardian.db')

def get_db_connection():
    """Create a connection to the SQLite database"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt=None):
    """Hash a password with SHA-256 and a random salt"""
    if salt is None:
        salt = uuid.uuid4().hex
    
    hashed_password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return salt, hashed_password

def initialize_database():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth TEXT,
        phone_number TEXT,
        address TEXT,
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    ''')
    
    # Emergency contacts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergency_contacts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        relationship TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        email TEXT,
        is_primary BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Medical history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        condition TEXT,
        diagnosis_date TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Test results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        test_type TEXT NOT NULL,
        test_date TEXT NOT NULL,
        prediction TEXT NOT NULL,
        confidence REAL NOT NULL,
        features TEXT NOT NULL,
        audio_file_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Doctor referrals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_referrals (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        doctor_name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        hospital TEXT,
        address TEXT,
        phone_number TEXT,
        email TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Doctors table - neurologists available for booking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone_number TEXT NOT NULL,
        specialization TEXT NOT NULL,
        sub_specialties TEXT,
        qualification TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        hospital_affiliation TEXT,
        clinic_address TEXT,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        consultation_fee REAL NOT NULL,
        about TEXT,
        profile_image_url TEXT,
        languages TEXT,
        rating REAL DEFAULT 0.0,
        total_reviews INTEGER DEFAULT 0,
        is_available BOOLEAN DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    ''')

    # Doctor availability schedule
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_availability (
        id TEXT PRIMARY KEY,
        doctor_id TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        slot_duration INTEGER DEFAULT 30,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')

    # Appointments/Bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        doctor_id TEXT NOT NULL,
        test_result_id TEXT,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'scheduled',
        booking_type TEXT NOT NULL DEFAULT 'consultation',
        symptoms TEXT,
        notes TEXT,
        risk_score INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        cancellation_reason TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id),
        FOREIGN KEY (test_result_id) REFERENCES test_results (id)
    )
    ''')

    # Doctor reviews
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_reviews (
        id TEXT PRIMARY KEY,
        doctor_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        appointment_id TEXT,
        rating INTEGER NOT NULL,
        review_text TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (appointment_id) REFERENCES appointments (id)
    )
    ''')

    conn.commit()
    conn.close()
    logging.info("Database initialized successfully")

def register_user(username, password, email, first_name, last_name, dob=None, phone=None, address=None):
    """Register a new user in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists"
        
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already registered"
        
        user_id = str(uuid.uuid4())
        salt, hashed_password = hash_password(password)
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO users (id, username, password_hash, salt, email, first_name, last_name, 
                          date_of_birth, phone_number, address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, hashed_password, salt, email, first_name, last_name, 
              dob, phone, address, created_at))
        
        conn.commit()
        conn.close()
        return True, user_id
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        return False, str(e)

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False, "Invalid username or password"
        
        salt = user['salt']
        stored_password = user['password_hash']
        
        _, hashed_password = hash_password(password, salt)
        
        if hashed_password == stored_password:
            # Update last login time
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                          (datetime.now().isoformat(), user['id']))
            conn.commit()
            conn.close()
            return True, dict(user)
        else:
            conn.close()
            return False, "Invalid username or password"
    except Exception as e:
        logging.error(f"Error authenticating user: {e}")
        return False, str(e)

def add_emergency_contact(user_id, name, relationship, phone, email=None, is_primary=False):
    """Add an emergency contact for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        contact_id = str(uuid.uuid4())
        
        # If this is a primary contact, unset any existing primary
        if is_primary:
            cursor.execute("UPDATE emergency_contacts SET is_primary = 0 WHERE user_id = ?", (user_id,))
        
        cursor.execute('''
        INSERT INTO emergency_contacts (id, user_id, name, relationship, phone_number, email, is_primary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contact_id, user_id, name, relationship, phone, email, is_primary))
        
        conn.commit()
        conn.close()
        return True, contact_id
    except Exception as e:
        logging.error(f"Error adding emergency contact: {e}")
        return False, str(e)

def save_test_result(user_id, test_type, prediction, confidence, features, audio_path=None):
    """Save a test result to the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        result_id = str(uuid.uuid4())
        test_date = datetime.now().isoformat()
        
        # Convert features dictionary to string
        features_str = str(features)
        
        cursor.execute('''
        INSERT INTO test_results (id, user_id, test_type, test_date, prediction, confidence, features, audio_file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (result_id, user_id, test_type, test_date, prediction, confidence, features_str, audio_path))
        
        conn.commit()
        conn.close()
        return True, result_id
    except Exception as e:
        logging.error(f"Error saving test result: {e}")
        return False, str(e)

def get_user_test_history(user_id):
    """Get all test results for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM test_results WHERE user_id = ? ORDER BY test_date DESC
        ''', (user_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, results
    except Exception as e:
        logging.error(f"Error retrieving test history: {e}")
        return False, str(e)

def get_user_emergency_contacts(user_id):
    """Get all emergency contacts for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM emergency_contacts WHERE user_id = ? ORDER BY is_primary DESC
        ''', (user_id,))

        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, contacts
    except Exception as e:
        logging.error(f"Error retrieving emergency contacts: {e}")
        return False, str(e)

# ============================================================================
# DOCTOR BOOKING SYSTEM FUNCTIONS
# ============================================================================

def add_doctor(full_name, email, phone_number, specialization, qualification,
               experience_years, city, state, consultation_fee,
               sub_specialties=None, hospital_affiliation=None, clinic_address=None,
               about=None, languages=None):
    """Add a new doctor to the system"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM doctors WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Doctor with this email already exists"

        doctor_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        cursor.execute('''
        INSERT INTO doctors (id, full_name, email, phone_number, specialization,
                           sub_specialties, qualification, experience_years,
                           hospital_affiliation, clinic_address, city, state,
                           consultation_fee, about, languages, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (doctor_id, full_name, email, phone_number, specialization,
              sub_specialties, qualification, experience_years,
              hospital_affiliation, clinic_address, city, state,
              consultation_fee, about, languages, created_at))

        conn.commit()
        conn.close()
        return True, doctor_id
    except Exception as e:
        logging.error(f"Error adding doctor: {e}")
        return False, str(e)

def get_all_doctors(city=None, specialization=None, is_available=True):
    """Get all doctors with optional filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM doctors WHERE 1=1"
        params = []

        if is_available:
            query += " AND is_available = ?"
            params.append(1)

        if city:
            query += " AND city = ?"
            params.append(city)

        if specialization:
            query += " AND specialization = ?"
            params.append(specialization)

        query += " ORDER BY rating DESC, experience_years DESC"

        cursor.execute(query, params)
        doctors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, doctors
    except Exception as e:
        logging.error(f"Error retrieving doctors: {e}")
        return False, str(e)

def get_doctor_by_id(doctor_id):
    """Get detailed information about a specific doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        doctor = cursor.fetchone()

        if not doctor:
            conn.close()
            return False, "Doctor not found"

        conn.close()
        return True, dict(doctor)
    except Exception as e:
        logging.error(f"Error retrieving doctor: {e}")
        return False, str(e)

def add_doctor_availability(doctor_id, day_of_week, start_time, end_time, slot_duration=30):
    """Add availability schedule for a doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        availability_id = str(uuid.uuid4())

        cursor.execute('''
        INSERT INTO doctor_availability (id, doctor_id, day_of_week, start_time,
                                        end_time, slot_duration)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (availability_id, doctor_id, day_of_week, start_time, end_time, slot_duration))

        conn.commit()
        conn.close()
        return True, availability_id
    except Exception as e:
        logging.error(f"Error adding doctor availability: {e}")
        return False, str(e)

def get_doctor_availability(doctor_id):
    """Get availability schedule for a doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM doctor_availability
        WHERE doctor_id = ? AND is_active = 1
        ORDER BY day_of_week, start_time
        ''', (doctor_id,))

        availability = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, availability
    except Exception as e:
        logging.error(f"Error retrieving doctor availability: {e}")
        return False, str(e)

def create_appointment(user_id, doctor_id, appointment_date, appointment_time,
                      test_result_id=None, symptoms=None, notes=None, risk_score=None):
    """Create a new appointment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        appointment_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        cursor.execute('''
        INSERT INTO appointments (id, user_id, doctor_id, test_result_id,
                                 appointment_date, appointment_time, status,
                                 symptoms, notes, risk_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (appointment_id, user_id, doctor_id, test_result_id,
              appointment_date, appointment_time, 'scheduled',
              symptoms, notes, risk_score, created_at))

        conn.commit()
        conn.close()
        return True, appointment_id
    except Exception as e:
        logging.error(f"Error creating appointment: {e}")
        return False, str(e)

def get_user_appointments(user_id, status=None):
    """Get all appointments for a user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
        SELECT a.*, d.full_name as doctor_name, d.specialization,
               d.hospital_affiliation, d.consultation_fee
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = ?
        '''
        params = [user_id]

        if status:
            query += " AND a.status = ?"
            params.append(status)

        query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"

        cursor.execute(query, params)
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, appointments
    except Exception as e:
        logging.error(f"Error retrieving user appointments: {e}")
        return False, str(e)

def get_doctor_appointments(doctor_id, appointment_date=None, status=None):
    """Get all appointments for a doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
        SELECT a.*, u.first_name, u.last_name, u.email, u.phone_number
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        WHERE a.doctor_id = ?
        '''
        params = [doctor_id]

        if appointment_date:
            query += " AND a.appointment_date = ?"
            params.append(appointment_date)

        if status:
            query += " AND a.status = ?"
            params.append(status)

        query += " ORDER BY a.appointment_date, a.appointment_time"

        cursor.execute(query, params)
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, appointments
    except Exception as e:
        logging.error(f"Error retrieving doctor appointments: {e}")
        return False, str(e)

def update_appointment_status(appointment_id, status, cancellation_reason=None):
    """Update appointment status (scheduled, completed, cancelled, no-show)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        updated_at = datetime.now().isoformat()

        cursor.execute('''
        UPDATE appointments
        SET status = ?, updated_at = ?, cancellation_reason = ?
        WHERE id = ?
        ''', (status, updated_at, cancellation_reason, appointment_id))

        conn.commit()
        conn.close()
        return True, "Appointment status updated"
    except Exception as e:
        logging.error(f"Error updating appointment: {e}")
        return False, str(e)

def add_doctor_review(doctor_id, user_id, rating, review_text=None, appointment_id=None):
    """Add a review for a doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        review_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        cursor.execute('''
        INSERT INTO doctor_reviews (id, doctor_id, user_id, appointment_id,
                                    rating, review_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (review_id, doctor_id, user_id, appointment_id, rating, review_text, created_at))

        # Update doctor's average rating
        cursor.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews
        FROM doctor_reviews
        WHERE doctor_id = ?
        ''', (doctor_id,))

        result = cursor.fetchone()
        avg_rating = result['avg_rating']
        total_reviews = result['total_reviews']

        cursor.execute('''
        UPDATE doctors
        SET rating = ?, total_reviews = ?, updated_at = ?
        WHERE id = ?
        ''', (avg_rating, total_reviews, created_at, doctor_id))

        conn.commit()
        conn.close()
        return True, review_id
    except Exception as e:
        logging.error(f"Error adding review: {e}")
        return False, str(e)

def get_doctor_reviews(doctor_id):
    """Get all reviews for a doctor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT r.*, u.first_name, u.last_name
        FROM doctor_reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.doctor_id = ?
        ORDER BY r.created_at DESC
        ''', (doctor_id,))

        reviews = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return True, reviews
    except Exception as e:
        logging.error(f"Error retrieving reviews: {e}")
        return False, str(e)

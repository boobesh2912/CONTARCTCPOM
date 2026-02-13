import gradio as gr
import os
import json
from datetime import datetime

from auth_routes import load_session, login_required, handle_logout, render_emergency_contacts
from db_utils import get_user_test_history, get_user_emergency_contacts

def format_date(iso_date):
    """Format ISO date to readable format"""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except:
        return iso_date

def dashboard():
    """Create dashboard components"""
    session = load_session()
    if not session or 'id' not in session:
        return gr.HTML("""
        <div style="text-align: center; padding: 20px;">
            <h2>Please log in to view your dashboard</h2>
        </div>
        """)
    
    user = session
    
    # Get user test history
    success, test_history = get_user_test_history(user['id'])
    if not success:
        test_history = []
    
    # Get emergency contacts
    success, contacts = get_user_emergency_contacts(user['id'])
    if not success:
        contacts = []
    
    # Dashboard Header
    with gr.Row():
        gr.HTML(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    padding: 15px; background-color: #1976d2; color: white; border-radius: 5px;">
            <div>
                <h2>Welcome, {user['first_name']} {user['last_name']}</h2>
                <p>Last login: {format_date(user.get('last_login', ''))}</p>
            </div>
            <div>
                <h3>MediGuardian Health Dashboard</h3>
            </div>
        </div>
        """)
    
    # Main Dashboard Content
    with gr.Tabs():
        # Profile Tab
        with gr.TabItem("Profile"):
            with gr.Row():
                with gr.Column():
                    gr.HTML(f"""
                    <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                        <h3>Personal Information</h3>
                        <table style="width: 100%;">
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Name:</td>
                                <td>{user['first_name']} {user['last_name']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Username:</td>
                                <td>{user['username']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Email:</td>
                                <td>{user['email']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Date of Birth:</td>
                                <td>{user.get('date_of_birth', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Phone:</td>
                                <td>{user.get('phone_number', '')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Address:</td>
                                <td>{user.get('address', '')}</td>
                            </tr>
                        </table>
                    </div>
                    """)
                
                with gr.Column():
                    gr.HTML(render_emergency_contacts(contacts))
                    gr.Button("Add/Manage Emergency Contacts")
        
        # Test History Tab
        with gr.TabItem("Test History"):
            if not test_history:
                gr.HTML("""
                <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                    <h3>No Test Results Yet</h3>
                    <p>You haven't taken any tests yet. Go to the Testing section to perform a new test.</p>
                </div>
                """)
            else:
                tests_html = """
                <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                    <h3>Your Test History</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #e0e0e0;">
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Test Type</th>
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Result</th>
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Confidence</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Actions</th>
                        </tr>
                """
                
                for test in test_history:
                    date = format_date(test['test_date'])
                    result_color = "#ffebee" if test['prediction'] == 'parkinsons' else "#e8f5e9"
                    confidence = f"{float(test['confidence']) * 100:.1f}%"
                    
                    tests_html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{test['test_type']}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background-color: {result_color};">{test['prediction'].capitalize()}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{confidence}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                            <button style="background-color: #1976d2; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                                View Details
                            </button>
                        </td>
                    </tr>
                    """
                
                tests_html += """
                    </table>
                </div>
                """
                gr.HTML(tests_html)
        
        # Take New Test Tab
        with gr.TabItem("Take New Test"):
            gr.HTML("""
            <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                <h3>Voice-Based Detection Tests</h3>
                <p>Please select a test type and follow the instructions to record your voice.</p>
            </div>
            """)
            
            with gr.Row():
                test_type = gr.Radio(
                    ["Parkinson's Disease Test", "Alzheimer's Disease Test (Coming Soon)", "ALS Test (Coming Soon)"],
                    label="Test Type",
                    value="Parkinson's Disease Test"
                )
            
            with gr.Row():
                audio_input = gr.Audio(type="filepath", label="Upload Voice Recording (.wav format)")
            
            gr.HTML("""
            <div style="padding: 15px; background-color: #e8f5e9; border-radius: 5px;">
                <h4>Recording Instructions:</h4>
                <ul>
                    <li>Record in a quiet environment with minimal background noise</li>
                    <li>Speak at a normal volume and pace</li>
                    <li>Record for at least 5 seconds of continuous speech</li>
                    <li>Sustained vowel sounds like "aaah" work best for analysis</li>
                    <li>Keep the microphone about 6 inches from your mouth</li>
                </ul>
            </div>
            """)
            
            analyze_button = gr.Button("Analyze Voice Recording")
            results_display = gr.HTML()
        
        # Doctor Referrals Tab
        with gr.TabItem("Find Specialists"):
            gr.HTML("""
            <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                <h3>Find Specialized Healthcare Providers</h3>
                <p>Connect with specialists based on your test results and location.</p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column():
                    specialty = gr.Radio(
                        ["Neurologist", "Parkinson's Specialist", "Movement Disorder Specialist", "Speech Therapist"],
                        label="Specialty",
                        value="Neurologist"
                    )
                    
                    location = gr.Textbox(label="Your Location (City, State or ZIP)")
                    
                    search_button = gr.Button("Search for Specialists")
                
                with gr.Column():
                    specialists_display = gr.HTML("""
                    <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                        <p>Enter your location and select a specialty to find healthcare providers near you.</p>
                    </div>
                    """)
    
    # Footer
    with gr.Row():
        logout_button = gr.Button("Logout")
        gr.HTML("""
        <div style="text-align: center; padding: 15px; margin-top: 20px; color: #666; font-size: 12px;">
            © 2025 MediGuardian - Early Detection for Neurodegenerative Diseases<br>
            This tool is for educational purposes only and should not replace professional medical advice.
        </div>
        """)
    
    # Set up event handlers
    logout_button.click(fn=handle_logout, inputs=[], outputs=[])
    
    return gr.HTML("Dashboard loaded")

@login_required
def analyze_voice_recording(audio_path, test_type):
    """Process the voice recording for the logged-in user"""
    from app import predict_parkinsons
    from db_utils import save_test_result
    
    if not audio_path:
        return """
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Please record or upload an audio file.
        </div>
        """
    
    try:
        if test_type == "Parkinson's Disease Test":
            result_html = predict_parkinsons(audio_path)
            
            # Extract prediction and confidence from the result HTML
            import re
            prediction_match = re.search(r'<b>Prediction:</b>\s*(\w+)', result_html)
            confidence_match = re.search(r'<b>Confidence:</b>\s*([\d.]+)%', result_html)
            
            if prediction_match and confidence_match:
                prediction = prediction_match.group(1).lower()
                confidence = float(confidence_match.group(1)) / 100
                
                # Save test result to database
                session = load_session()
                if session and 'id' in session:
                    # Parse features from the analysis
                    features = {}
                    jitter_match = re.search(r'<b>Jitter \(frequency variation\):</b>\s*([\d.]+)', result_html)
                    shimmer_match = re.search(r'<b>Shimmer \(amplitude variation\):</b>\s*([\d.]+)', result_html)
                    hnr_match = re.search(r'<b>Harmonic-to-Noise Ratio:</b>\s*([\d.]+)', result_html)
                    
                    if jitter_match:
                        features['jitter_relative'] = float(jitter_match.group(1))
                    if shimmer_match:
                        features['shimmer_relative'] = float(shimmer_match.group(1))
                    if hnr_match:
                        features['hnr'] = float(hnr_match.group(1))
                    
                    save_test_result(
                        session['id'], 
                        'parkinsons', 
                        prediction, 
                        confidence, 
                        features, 
                        audio_path
                    )
                    
                    # Enhance the result with alert for severe cases
                    if prediction == 'parkinsons' and confidence > 0.8:
                        result_html += """
                        <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 5px solid #c62828;">
                            <h3>High Confidence Detection - Alert Sent</h3>
                            <p>Due to the high confidence in this result, we've sent an automatic notification to your primary emergency contact.</p>
                            <p>We recommend scheduling an appointment with a specialist as soon as possible.</p>
                        </div>
                        """
                        
                        # In a real system, you would trigger an alert to emergency contacts here
                        # For now, we just display a message indicating this would happen
            
            return result_html
        else:
            # For future test types
            return """
            <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                <h3>Coming Soon</h3>
                <p>This test type is currently under development. Please check back later.</p>
            </div>
            """
    except Exception as e:
        return f"""
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Error processing audio: {str(e)}
        </div>
        """

def find_specialists(specialty, location):
    """Find healthcare specialists based on specialty and location"""
    if not specialty or not location:
        return """
        <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
            <p>Please select a specialty and enter your location to find healthcare providers.</p>
        </div>
        """
    
    # This would normally query a database or API, but for demo purposes we'll return mock data
    specialists = {
        "Neurologist": [
            {
                "name": "Dr. Sarah Johnson",
                "practice": "Neurology Associates",
                "address": "123 Medical Center Dr, Springfield",
                "phone": "(555) 123-4567",
                "rating": 4.8,
                "specialties": ["Movement Disorders", "Parkinson's Disease"]
            },
            {
                "name": "Dr. Michael Chen",
                "practice": "University Medical Center",
                "address": "456 Hospital Blvd, Springfield",
                "phone": "(555) 987-6543",
                "rating": 4.9,
                "specialties": ["Neurodegenerative Disorders", "Clinical Trials"]
            }
        ],
        "Parkinson's Specialist": [
            {
                "name": "Dr. Robert Patel",
                "practice": "Movement Disorder Clinic",
                "address": "789 Health Parkway, Springfield",
                "phone": "(555) 456-7890",
                "rating": 4.7,
                "specialties": ["Parkinson's Disease", "Deep Brain Stimulation"]
            }
        ],
        "Movement Disorder Specialist": [
            {
                "name": "Dr. Lisa Thompson",
                "practice": "Advanced Movement Care",
                "address": "321 Wellness Ave, Springfield",
                "phone": "(555) 789-0123",
                "rating": 4.6,
                "specialties": ["Movement Disorders", "Gait Analysis"]
            }
        ],
        "Speech Therapist": [
            {
                "name": "Amanda Wilson, SLP",
                "practice": "Speech & Voice Rehabilitation",
                "address": "567 Therapy Ct, Springfield",
                "phone": "(555) 234-5678",
                "rating": 4.9,
                "specialties": ["Voice Disorders", "Parkinson's Speech Therapy"]
            }
        ]
    }
    
    if specialty in specialists:
        specialists_list = specialists[specialty]
        html = f"""
        <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
            <h3>Specialists Near {location}</h3>
            <p>Found {len(specialists_list)} {specialty}(s) in your area:</p>
        """
        
        for doctor in specialists_list:
            stars = "★" * int(doctor["rating"]) + "☆" * (5 - int(doctor["rating"]))
            specialties = ", ".join(doctor["specialties"])
            
            html += f"""
            <div style="margin-top: 15px; padding: 15px; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4>{doctor["name"]}</h4>
                <p><strong>{doctor["practice"]}</strong></p>
                <p>{doctor["address"]}</p>
                <p>Phone: {doctor["phone"]}</p>
                <p>Rating: {stars} ({doctor["rating"]})</p>
                <p>Specialties: {specialties}</p>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button style="background-color: #1976d2; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer;">
                        Schedule Consultation
                    </button>
                    <button style="background-color: white; color: #1976d2; border: 1px solid #1976d2; padding: 8px 15px; border-radius: 3px; cursor: pointer;">
                        View Profile
                    </button>
                </div>
            </div>
            """
        
        html += """
        </div>
        """
        return html
    else:
        return """
        <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
            <p>No specialists found for the selected criteria. Please try a different specialty or location.</p>
        </div>
        """
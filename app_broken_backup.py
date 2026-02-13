import os
import numpy as np
import pandas as pd
import joblib
import gradio as gr
import librosa
import matplotlib.pyplot as plt
import seaborn as sns
from utils.advanced_features import extract_advanced_features
from db_utils import initialize_database
from auth_routes import login_form, register_form, emergency_contact_form
from auth_routes import handle_login, handle_register, handle_add_emergency_contact
from auth_routes import load_session, clear_session
from dashboard import dashboard, analyze_voice_recording, find_specialists
import warnings
warnings.filterwarnings('ignore')

def analyze_audio_file(audio_file):
    """Process audio file and extract visualizations and features"""
    y, sr = librosa.load(audio_file)
    os.makedirs('temp', exist_ok=True)
    plt.figure(figsize=(12, 4))
    plt.plot(np.linspace(0, len(y)/sr, len(y)), y)
    plt.title('Audio Waveform')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.savefig('temp/waveform.png')
    plt.close()
    plt.figure(figsize=(12, 6))
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.tight_layout()
    plt.savefig('temp/spectrogram.png')
    plt.close()
    features = extract_advanced_features(y, sr)
    return y, sr, features

def predict_parkinsons(audio_path):
    """Process audio file without quality checks to ensure dataset files are analyzed"""
    y, sr = librosa.load(audio_path)
    try:
        if not os.path.exists('models/parkinson_model.pkl'):
            return "Error: Model not found. Please run the training script first."
        model = joblib.load('models/parkinson_model.pkl')
        y, sr, features = analyze_audio_file(audio_path)
        feature_names = []
        if os.path.exists('models/feature_names.txt'):
            with open('models/feature_names.txt', 'r') as f:
                feature_names = f.read().splitlines()
        if feature_names:
            feature_values = []
            for feature_name in feature_names:
                feature_values.append(features.get(feature_name, 0))
            feature_array = np.array([feature_values])
        else:
            features_df = pd.DataFrame([features])
            if 'filename' in features_df.columns:
                features_df = features_df.drop('filename', axis=1)
            if 'label' in features_df.columns:
                features_df = features_df.drop('label', axis=1)
            feature_array = features_df.values
        prediction = 'healthy'
        confidence = 0.5
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(feature_array)[0]
            parkinsons_probability = probability[1] if len(probability) > 1 else 0.5
            if parkinsons_probability > 0.7:
                prediction = 'parkinsons'
                confidence = parkinsons_probability
            else:
                prediction = 'healthy'
                confidence = 1 - parkinsons_probability
        else:
            raw_prediction = model.predict(feature_array)[0]
            prediction = raw_prediction
            confidence = 0.8  
        result = f"""
        <h2>Parkinson's Disease Analysis Results</h2>
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div>
                <h3>Audio Visualization</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <p><b>Waveform:</b></p>
                        <img src="file/temp/waveform.png" alt="Audio Waveform" style="max-width: 100%; height: auto;">
                    </div>
                    <div>
                        <p><b>Spectrogram:</b></p>
                        <img src="file/temp/spectrogram.png" alt="Audio Spectrogram" style="max-width: 100%; height: auto;">
                    </div>
                </div>
            </div>
            <div>
                <h3>Analysis Results</h3>
                <p><b>Prediction:</b> {prediction.capitalize()}</p>
                <p><b>Confidence:</b> {confidence:.2%}</p>
                <div style="background-color: {'#ffebee' if prediction == 'parkinsons' else '#e8f5e9'}; padding: 15px; border-radius: 5px; margin-top: 15px;">
                    <h4>{'Parkinson\'s Disease Indicators Detected' if prediction == 'parkinsons' else 'No Parkinson\'s Disease Indicators Detected'}</h4>
                    <h4>Key Voice Characteristics:</h4>
                    <ul>
                        <li><b>Jitter (frequency variation):</b> {features.get('jitter_relative', 0):.5f} {'(Elevated)' if features.get('jitter_relative', 0) > 0.01 and prediction == 'parkinsons' else '(Normal)'}</li>
                        <li><b>Shimmer (amplitude variation):</b> {features.get('shimmer_relative', 0):.5f} {'(Elevated)' if features.get('shimmer_relative', 0) > 0.06 and prediction == 'parkinsons' else '(Normal)'}</li>
                        <li><b>Harmonic-to-Noise Ratio:</b> {features.get('hnr', 0):.2f} dB {'(Reduced)' if features.get('hnr', 0) < 10 and prediction == 'parkinsons' else '(Normal)'}</li>
                    </ul>
                    <h4>Recommendations:</h4>
                    <ul>
                        {'<li>Consult with a neurologist for a comprehensive evaluation</li><li>Monitor symptoms and keep a daily log</li><li>Consider regular physical therapy and exercise</li><li>Join a Parkinson\'s support group</li>' 
                        if prediction == 'parkinsons' else 
                        '<li>Continue regular health check-ups</li><li>Maintain an active lifestyle</li><li>Consider periodic voice assessments every 6-12 months</li><li>Stay hydrated for vocal health</li>'}
                    </ul>
                </div>
            </div>
        </div>
        """
        return result
    except Exception as e:
        return f"Error analyzing audio: {str(e)}"
def get_disease_info():
    """Return information about various neurodegenerative diseases"""
    diseases = {
        "parkinsons": {
            "name": "Parkinson's Disease",
            "description": "A progressive nervous system disorder that affects movement, often including tremors.",
            "symptoms": ["Tremor", "Bradykinesia (slow movement)", "Rigid muscles", "Impaired posture and balance", "Loss of automatic movements", "Speech changes"],
            "video_id": "H_F7OxMEz90",
            "color": "#E91E63"
        },
        "alzheimers": {
            "name": "Alzheimer's Disease",
            "description": "A progressive disorder that causes brain cells to degenerate and die.",
            "symptoms": ["Memory loss", "Difficulty thinking and understanding", "Confusion", "Changes in behavior", "Difficulty speaking, swallowing or walking"],
            "video_id": "wfGqbN5VmLo",
            "color": "#3F51B5"
        },
        "huntingtons": {
            "name": "Huntington's Disease",
            "description": "A rare, inherited disease that causes the progressive breakdown of nerve cells in the brain.",
            "symptoms": ["Involuntary jerking movements", "Muscle problems", "Difficulty walking", "Cognitive difficulties", "Psychiatric disorders"],
            "video_id": "nJoS5MODfe0",
            "color": "#009688"
        },
        "als": {
            "name": "Amyotrophic Lateral Sclerosis (ALS)",
            "description": "A progressive nervous system disease that affects nerve cells in the brain and spinal cord, causing loss of muscle control.",
            "symptoms": ["Difficulty walking", "Weakness in legs, feet or ankles", "Hand weakness or clumsiness", "Slurred speech", "Muscle cramps and twitching"],
            "video_id": "elTbHnJ-Y8E",
            "color": "#FF5722"
        },
        "ms": {
            "name": "Multiple Sclerosis",
            "description": "A disease in which the immune system eats away at the protective covering of nerves.",
            "symptoms": ["Numbness or weakness in limbs", "Electric-shock sensations", "Tremor", "Vision problems", "Slurred speech", "Fatigue"],
            "video_id": "yzH8ut6ChMc",
            "color": "#673AB7"
        }
    }
    return diseases
def create_app():
    """Create and configure the Gradio application with authentication"""
    # Initialize database
    initialize_database()
    
    # Check if user is logged in
    session = load_session()
    
    # Define the page rendering based on URL parameters
    def render_page():
        # Central state for tracking current page
        page_state = gr.State("dashboard" if session else "test")

        with gr.Blocks(css="""
            .gradio-container {
                max-width: 100% !important;
                padding: 0 !important;
            }
            
            .main-container {
                font-family: 'Poppins', sans-serif;
            }
            
            .modern-button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 12px 24px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
                transition: all 0.3s;
            }
            
            .modern-button:hover {
                background-color: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                padding: 20px;
                margin: 15px 0;
                transition: all 0.3s;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }
            
            .nav-link {
                font-weight: 500;
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 4px;
                transition: all 0.3s;
            }
            
            .nav-link:hover {
                background-color: rgba(255,255,255,0.2);
            }
            
            .footer {
                background-color: #333;
                color: white;
                text-align: center;
                padding: 20px 0;
                margin-top: 50px;
            }
            
            /* Form Styling */
            input[type=text], input[type=password], input[type=email], input[type=date], select, textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
                margin-top: 6px;
                margin-bottom: 16px;
                resize: vertical;
                font-family: 'Poppins', sans-serif;
            }
            
            /* Disease Cards */
            .disease-card {
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                color: white;
                transition: all 0.3s;
            }
            
            .disease-card:hover {
                transform: scale(1.02);
            }
            
            .video-container {
                position: relative;
                padding-bottom: 56.25%;
                height: 0;
                overflow: hidden;
                max-width: 100%;
                margin: 20px 0;
                border-radius: 8px;
            }
            
            .video-container iframe {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 8px;
            }
        """) as demo:
            # Navigation and page management
            with gr.Row():
                with gr.Column(scale=10):
                    gr.HTML("""
                    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
                    <div style="display: flex; align-items: center; padding: 15px 20px; background: linear-gradient(135deg, #1976d2, #0d47a1); color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px;">
                        <h1 style="margin: 0; font-size: 28px; font-family: 'Poppins', sans-serif; font-weight: 600; flex: 1;">
                            <span style="color: #4CAF50;">Medi</span>Guardian
                        </h1>
                        <span style="font-size: 14px; font-weight: 300;">Early Detection for Neurodegenerative Diseases</span>
                    </div>
                    """)
                with gr.Column(scale=1):
                    pass  # Spacer
            
            # Page content - all pages defined here
            with gr.Group() as main_content:
                # Login Page
                with gr.Blocks() as login_page:
                gr.HTML("""
                <div class="main-container" style="display: flex; flex-direction: column; align-items: center; margin: 40px 0;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="font-size: 36px; color: #1976d2; font-weight: 600; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">
                            Welcome to MediGuardian
                        </h2>
                        <p style="font-size: 18px; color: #666; max-width: 600px; margin: 0 auto; font-family: 'Poppins', sans-serif;">
                            Your personal health assistant for early detection and management of neurodegenerative conditions
                        </p>
                    </div>
                    <div style="display: flex; width: 100%; max-width: 1200px; gap: 40px; margin: 0 auto; padding: 0 20px;">
                        <div style="flex: 1; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                            <h3 style="color: #1976d2; font-family: 'Poppins', sans-serif; font-weight: 500; margin-bottom: 20px;">Log In</h3>
                            <div id="login-form-container"></div>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                            <div style="background: linear-gradient(135deg, #4CAF50, #2E7D32); color: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
                                <h3 style="font-family: 'Poppins', sans-serif; font-weight: 500; margin-bottom: 20px;">Why MediGuardian?</h3>
                                <ul style="padding-left: 20px; font-family: 'Poppins', sans-serif;">
                                    <li style="margin-bottom: 10px;">Early detection increases treatment effectiveness</li>
                                    <li style="margin-bottom: 10px;">Non-invasive voice analysis technology</li>
                                    <li style="margin-bottom: 10px;">Track your health progress over time</li>
                                    <li style="margin-bottom: 10px;">Connect with specialists in your area</li>
                                    <li>Access personalized exercise recommendations</li>
                                </ul>
                                <div style="margin-top: 30px;">
                                    <p style="font-family: 'Poppins', sans-serif;">Don't have an account?</p>
                                    <button id="create-account-btn" style="background-color: white; color: #4CAF50; border: none; padding: 12px 24px; border-radius: 5px; font-weight: 500; cursor: pointer; font-family: 'Poppins', sans-serif; margin-top: 10px; transition: all 0.3s;">
                                        Create New Account
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <script>
                    document.getElementById('create-account-btn').addEventListener('click', function() {
                        // Hide login page and show register page
                        // This will be handled by Gradio's event system
                        document.getElementById('register-link-hidden').click();
                    });
                </script>
                """)
                login_components = login_form()
                # Hidden button to trigger the register link click event (click handler attached after register_page exists)
                register_link_hidden = gr.Button("Register", elem_id="register-link-hidden", visible=False)

            # Register Page
            with gr.Blocks(visible=False) as register_page:
                gr.HTML("""
                <div class="main-container" style="display: flex; flex-direction: column; align-items: center; margin: 40px 0;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="font-size: 32px; color: #1976d2; font-weight: 600; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">
                            Create Your MediGuardian Account
                        </h2>
                        <p style="font-size: 16px; color: #666; max-width: 600px; margin: 0 auto; font-family: 'Poppins', sans-serif;">
                            Join our community and take control of your health journey
                        </p>
                    </div>
                    <div style="width: 100%; max-width: 800px; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 0 auto;">
                        <div id="register-form-container"></div>
                        <button id="back-to-login-btn" style="background-color: #f5f5f5; color: #333; border: none; padding: 10px 20px; border-radius: 5px; font-weight: 500; cursor: pointer; font-family: 'Poppins', sans-serif; margin-top: 20px; transition: all 0.3s;">
                            Back to Login
                        </button>
                    </div>
                </div>
                <script>
                    document.getElementById('back-to-login-btn').addEventListener('click', function() {
                        // This will be handled by Gradio's event system
                        document.getElementById('back-button-hidden').click();
                    });
                </script>
                """)
                register_components = register_form()
                # Hidden button to trigger the back button event
                back_button_hidden = gr.Button("Back", elem_id="back-button-hidden", visible=False)
                back_button_hidden.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)), 
                    inputs=[], 
                    outputs=[register_page, login_page]
                )
                # Now that register_page exists, attach the register_link_hidden click handler
                register_link_hidden.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)), 
                    inputs=[], 
                    outputs=[login_page, register_page]
                )
            
            # Emergency Contact Management Page
            with gr.Blocks(visible=False) as contact_page:
                gr.HTML("""
                <div class="main-container" style="display: flex; flex-direction: column; align-items: center; margin: 40px 0;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="font-size: 32px; color: #1976d2; font-weight: 600; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">
                            Emergency Contacts
                        </h2>
                        <p style="font-size: 16px; color: #666; max-width: 600px; margin: 0 auto; font-family: 'Poppins', sans-serif;">
                            Add trusted contacts who should be notified in case of concerning test results
                        </p>
                    </div>
                    <div style="width: 100%; max-width: 800px; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 0 auto;">
                        <div id="contact-form-container"></div>
                    </div>
                </div>
                """)
                contact_components = emergency_contact_form()
                # Deferred: click handler attached after dashboard_page is defined
                contact_return_btn = gr.Button("Return to Dashboard", elem_id="contact-return-btn", elem_classes="modern-button")
            
            # Dashboard Page with enhanced neurodegenerative disease information
            with gr.Blocks(visible=False) as dashboard_page:
                diseases = get_disease_info()
                disease_html = ""
                
                for disease_id, disease in diseases.items():
                    disease_html += f"""
                    <div class="card" style="margin-bottom: 40px;">
                        <div class="disease-card" style="background: linear-gradient(135deg, {disease['color']}, {disease['color']}CC);">
                            <h3 style="font-size: 24px; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">{disease['name']}</h3>
                            <p style="font-size: 16px; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">{disease['description']}</p>
                        </div>
                        
                        <div style="padding: 20px 0;">
                            <h4 style="font-size: 18px; color: #333; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">Common Symptoms:</h4>
                            <ul style="padding-left: 20px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
                            """
                    
                    for symptom in disease['symptoms']:
                        disease_html += f'<li style="margin-bottom: 5px;">{symptom}</li>'
                    
                    disease_html += f"""
                            </ul>
                            
                            <h4 style="font-size: 18px; color: #333; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">Recommended Exercises:</h4>
                            <div class="video-container">
                                <iframe width="560" height="315" src="https://www.youtube.com/embed/{disease['video_id']}" 
                                    title="{disease['name']} Exercises" frameborder="0" 
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                    allowfullscreen></iframe>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                                <button class="modern-button" style="background-color: {disease['color']};">Take {disease['name']} Test</button>
                                <button class="modern-button" style="background-color: #757575;">Find Specialists</button>
                            </div>
                        </div>
                    </div>
                    """
                
                gr.HTML(f"""
                <div class="main-container" style="padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                        <h2 style="font-size: 32px; color: #1976d2; font-weight: 600; font-family: 'Poppins', sans-serif;">
                            Your Health Dashboard
                        </h2>
                        <div>
                            <button id="add-emergency-contact-btn" class="modern-button" style="margin-right: 10px;">
                                Emergency Contacts
                            </button>
                            <button id="logout-btn" class="modern-button" style="background-color: #f44336;">
                                Logout
                            </button>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
                        <!-- Left sidebar -->
                        <div>
                            <div class="card">
                                <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                                    Quick Test
                                </h3>
                                <p style="margin-bottom: 20px; color: #666; font-family: 'Poppins', sans-serif;">
                                    Record a quick voice sample to check for early indicators
                                </p>
                                <div id="quick-test-container"></div>
                                <button class="modern-button" style="width: 100%; margin-top: 15px;">
                                    Start Quick Voice Test
                                </button>
                            </div>
                            
                            <div class="card" style="margin-top: 20px;">
                                <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                                    Your Progress
                                </h3>
                                <p style="margin-bottom: 20px; color: #666; font-family: 'Poppins', sans-serif;">
                                    Track your health metrics over time
                                </p>
                                <div style="background-color: #f5f5f5; border-radius: 8px; padding: 15px; text-align: center;">
                                    <p style="font-family: 'Poppins', sans-serif;">Last test: <span style="font-weight: 500;">April 10, 2025</span></p>
                                    <p style="font-family: 'Poppins', sans-serif;">Status: <span style="color: #4CAF50; font-weight: 500;">Healthy</span></p>
                                </div>
                            </div>
                            
                            <div class="card" style="margin-top: 20px;">
                                <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                                    Find Specialists
                                </h3>
                                <p style="margin-bottom: 20px; color: #666; font-family: 'Poppins', sans-serif;">
                                    Connect with healthcare providers near you
                                </p>
                                <button class="modern-button" style="width: 100%;">
                                    Search Specialists
                                </button>
                            </div>
                        </div>
                        
                        <!-- Main content -->
                        <div>
                            <div class="card">
                                <h3 style="font-size: 24px; color: #333; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
                                    Neurodegenerative Diseases
                                </h3>
                                
                                {disease_html}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p style="font-family: 'Poppins', sans-serif;">&copy; 2025 MediGuardian. All rights reserved.</p>
                    <p style="font-size: 14px; margin-top: 5px; font-family: 'Poppins', sans-serif;">
                        Disclaimer: This application is intended for educational purposes only and should not replace professional medical advice.
                    </p>
                </div>
                
                <script>
                    document.getElementById('add-emergency-contact-btn').addEventListener('click', function() {{
                        document.getElementById('emergency-contact-btn-hidden').click();
                    }});
                </script>
                """)
                dashboard_components = dashboard()
                emergency_contact_btn_hidden = gr.Button("Emergency Contacts", elem_id="emergency-contact-btn-hidden", visible=False)
                # Deferred: click handler attached after contact_page is defined (happens below)
                # Now attach deferred click handlers after all pages are defined
                contact_return_btn.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
                    inputs=[],
                    outputs=[contact_page, dashboard_page]
                )
                emergency_contact_btn_hidden.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
                    inputs=[],
                    outputs=[dashboard_page, contact_page]
                )
            with gr.Blocks(visible=False) as public_test_page:
                gr.HTML("""
                <div class="main-container" style="padding: 20px; max-width: 1200px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="font-size: 32px; color: #1976d2; font-weight: 600; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">
                            Parkinson's Disease Voice Analysis
                        </h2>
                        <p style="font-size: 16px; color: #666; max-width: 800px; margin: 0 auto 20px; font-family: 'Poppins', sans-serif;">
                            Our advanced AI analyzes subtle voice characteristics to detect early indicators of Parkinson's Disease
                        </p>
                    </div>
                    
                    <div class="card">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                            <div>
                                <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                                    Upload or Record Voice Sample
                                </h3>
                                <div id="audio-input-container"></div>
                                <div id="analyze-button-container" style="margin-top: 20px;"></div>
                            </div>
                            
                            <div>
                                <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                                    Recording Guidelines
                                </h3>
                                <ul style="padding-left: 20px; margin-bottom: 20px; font-family: 'Poppins', sans-serif;">
                                    <li style="margin-bottom: 10px;">Record in a quiet environment with minimal background noise</li>
                                    <li style="margin-bottom: 10px;">Speak at a normal volume and pace</li>
                                    <li style="margin-bottom: 10px;">Record for at least 5 seconds of continuous speech</li>
                                    <li style="margin-bottom: 10px;">Sustained vowel sounds like "aaah" work best for analysis</li>
                                    <li>Keep the microphone about 6 inches from your mouth</li>
                                </ul>
                                <div style="background-color: #e8f5e9; border-radius: 8px; padding: 15px; margin-top: 20px;">
                                    <h4 style="color: #2E7D32; margin-bottom: 10px; font-family: 'Poppins', sans-serif;">Why Voice Analysis?</h4>
                                    <p style="font-family: 'Poppins', sans-serif;">
                                        Voice changes often occur in the early stages of Parkinson's Disease, even before other 
                                        motor symptoms become apparent. Our algorithm analyzes subtle vocal characteristics 
                                        like jitter, shimmer, and harmonic-to-noise ratio that may indicate neurological changes.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="result-output-container" style="margin-top: 30px;"></div>
                    
                    <div class="card" style="margin-top: 30px;">
                        <h3 style="font-size: 22px; color: #333; margin-bottom: 15px; font-family: 'Poppins', sans-serif;">
                            Sample Recordings
                        </h3>
                        <p style="margin-bottom: 20px; color: #666; font-family: 'Poppins', sans-serif;">
                            Click to analyze pre-recorded samples for demonstration purposes:
                        </p>
                        <div id="examples-container"></div>
                    </div>
                    
                    <div class="footer">
                        <p style="font-family: 'Poppins', sans-serif;">&copy; 2025 MediGuardian. All rights reserved.</p>
                        <p style="font-size: 14px; margin-top: 5px; font-family: 'Poppins', sans-serif;">
                            Disclaimer: This tool is intended for educational purposes only and should not replace professional medical advice.
                            Many factors can affect voice quality including fatigue, illness, and recording conditions.
                        </p>
                    </div>
                </div>
                """)
                
                audio_input = gr.Audio(type="filepath", label="Upload or Record Voice (.wav format)")
                analyze_button = gr.Button("Analyze Voice Sample", elem_id="analyze-button", elem_classes="modern-button")
                result_output = gr.HTML()
                
                analyze_button.click(
                    fn=predict_parkinsons,
                    inputs=[audio_input],
                    outputs=[result_output]
                )
                
                examples = []
                if os.path.exists("data/HC_AH") and os.listdir("data/HC_AH") and os.path.exists("data/PD_AH") and os.listdir("data/PD_AH"):
                    examples = [["data/HC_AH/HC_AH_1.wav"], ["data/PD_AH/PD_AH_1.wav"]]
                
                if examples:
                    gr.Examples(examples=examples, inputs=[audio_input])
            login_components["login_button"].click(
                fn=handle_login,
                inputs=[login_components["username"], login_components["password"]],
                outputs=[login_components["login_message"]]
            )
            login_components["register_link"].click(
                fn=lambda: gr.update(visible=False), 
                inputs=[], 
                outputs=[login_page]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[register_page]
            )
            register_components["register_button"].click(
                fn=handle_register,
                inputs=[
                    register_components["username"],
                    register_components["password"],
                    register_components["confirm_password"],
                    register_components["email"],
                    register_components["first_name"],
                    register_components["last_name"],
                    register_components["dob"],
                    register_components["phone"],
                    register_components["address"]
                ],
                outputs=[register_components["register_message"]]
            )
            register_components["back_button"].click(
                fn=lambda: gr.update(visible=False),
                inputs=[],
                outputs=[register_page]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[login_page]
            )
            contact_components["add_button"].click(
                fn=handle_add_emergency_contact,
                inputs=[
                    contact_components["name"],
                    contact_components["relationship"],
                    contact_components["phone"],
                    contact_components["email"],
                    contact_components["is_primary"]
                ],
                outputs=[contact_components["contact_message"], contact_components["contact_list"]]
            )
            def route_page(url_params):
                pages = {
                    "login": login_page,
                    "register": register_page,
                    "dashboard": dashboard_page if session else login_page,
                    "contacts": contact_page if session else login_page,
                    "test": public_test_page
                }
                
                page = "test"  # Default page for non-logged in users
                if session:
                    page = "dashboard"  # Default for logged in users
                
                # Parse URL parameters
                if url_params:
                    try:
                        params = dict(item.split("=") for item in url_params.split("&") if "=" in item)
                        if "page" in params:
                            page = params["page"]
                    except:
                        pass
                
                # Update page visibility
                updates = []
                for page_name, page_block in pages.items():
                    updates.append(gr.update(visible=(page == page_name)))
                
                return updates
            
            # Initial page load and URL change handler
            demo.load(
                fn=route_page,
                inputs=[url_params],
                outputs=[login_page, register_page, dashboard_page, contact_page, public_test_page]
            )
        
        return demo
    
    # Create the Gradio interface
    interface = render_page()
    
    return interface

if __name__ == "__main__":
    app = create_app()
    app.launch(share=True)

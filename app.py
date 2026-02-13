"""
MediGuardian - Clean, Bug-Free Frontend with Proper Backend Integration
"""
import os
import numpy as np
import pandas as pd
import joblib
import gradio as gr
import librosa
from librosa import display as librosa_display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from utils.advanced_features import extract_advanced_features
from db_utils import initialize_database
from auth_routes import (
    login_form, register_form, emergency_contact_form,
    handle_login, handle_register, handle_add_emergency_contact,
    load_session, clear_session
)
from dashboard import dashboard, analyze_voice_recording, find_specialists
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')


def analyze_audio_file(audio_file):
    """Process audio file and extract visualizations and features"""
    y, sr = librosa.load(audio_file)
    os.makedirs(TEMP_DIR, exist_ok=True)
    plt.figure(figsize=(12, 4))
    plt.plot(np.linspace(0, len(y)/sr, len(y)), y)
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


def predict_parkinsons(audio_path):
    """Predict Parkinson's disease from audio"""
    if not audio_path:
        return "Error: Please upload or record an audio file."
    try:
        model_path = os.path.join(MODELS_DIR, 'parkinson_model.pkl')
        feature_names_path = os.path.join(MODELS_DIR, 'feature_names.txt')

        if not os.path.exists(model_path):
            return "Error: Model not found. Please run train_model.py first."
        model = joblib.load(model_path)
        y, sr, features = analyze_audio_file(audio_path)
        feature_names = []
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
        
        prediction = 'healthy'
        confidence = 0.5
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(feature_array)[0]
            parkinsons_prob = probability[1] if len(probability) > 1 else 0.5
            prediction = 'parkinsons' if parkinsons_prob > 0.7 else 'healthy'
            confidence = parkinsons_prob if prediction == 'parkinsons' else (1 - parkinsons_prob)
        else:
            prediction = model.predict(feature_array)[0]
            confidence = 0.8
        
        # Format result with professional SaaS styling
        is_parkinsons = prediction == 'parkinsons'
        alert_icon = "⚠" if is_parkinsons else "✓"
        alert_msg = "Parkinsons Indicators Detected" if is_parkinsons else "No Indicators Detected"
        status_color = "#D32F2F" if is_parkinsons else "#388E3C"
        bg_color = "#FFEBEE" if is_parkinsons else "#E8F5E9"
        border_color = "#EF5350" if is_parkinsons else "#66BB6A"
        
        jitter_val = features.get("jitter_relative", 0)
        shimmer_val = features.get("shimmer_relative", 0)
        hnr_val = features.get("hnr", 0)
        f0_mean = features.get("f0_mean", 0)
        
        confidence_pct = confidence * 100
        
        # Get absolute paths for Gradio file serving
        waveform_path = os.path.join(TEMP_DIR, 'waveform.png')
        spectrogram_path = os.path.join(TEMP_DIR, 'spectrogram.png')
        
        # Modern SaaS result card with proper styling
        result = f"""
        <style>
            .result-container {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            .result-header {{
                background: linear-gradient(135deg, #1976D2, #0D47A1);
                color: white;
                padding: 24px;
                border-radius: 8px 8px 0 0;
                margin: 0;
            }}
            .result-header h2 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .result-content {{
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 0 0 8px 8px;
                padding: 24px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }}
            .result-status {{
                background-color: {bg_color};
                border-left: 5px solid {status_color};
                padding: 20px;
                border-radius: 6px;
                margin: 16px 0;
            }}
            .result-status-title {{
                color: {status_color};
                font-size: 20px;
                font-weight: 600;
                margin: 0 0 12px 0;
            }}
            .result-status-icon {{
                font-size: 24px;
                margin-right: 8px;
            }}
            .confidence-bar {{
                background: #F5F5F5;
                border-radius: 4px;
                height: 32px;
                margin: 12px 0;
                overflow: hidden;
                display: flex;
                align-items: center;
            }}
            .confidence-fill {{
                background: linear-gradient(90deg, {status_color}, {status_color}dd);
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 14px;
                width: {confidence_pct}%;
                transition: width 0.3s ease;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: #F9F9F9;
                padding: 16px;
                border-radius: 6px;
                border: 1px solid #E0E0E0;
                text-align: center;
            }}
            .metric-label {{
                color: #666;
                font-size: 13px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}
            .metric-value {{
                color: #1976D2;
                font-size: 24px;
                font-weight: 700;
            }}
            .visualization-section {{
                margin: 24px 0;
            }}
            .visualization-section h3 {{
                color: #1976D2;
                font-size: 18px;
                font-weight: 600;
                margin: 16px 0 12px 0;
            }}
            .images-row {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
                margin: 16px 0;
            }}
            .image-box {{
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
                text-align: center;
            }}
            .image-box img {{
                max-width: 100%;
                height: auto;
                border-radius: 4px;
                display: block;
            }}
            .image-label {{
                color: #666;
                font-size: 13px;
                font-weight: 500;
                margin-top: 8px;
            }}
            .info-box {{
                background: #E3F2FD;
                border-left: 4px solid #1976D2;
                padding: 12px 16px;
                border-radius: 4px;
                margin: 12px 0;
                color: #0D47A1;
                font-size: 13px;
            }}
        </style>
        
        <div class="result-container">
            <div class="result-header">
                <h2>Parkinson's Disease Analysis Results</h2>
            </div>
            
            <div class="result-content">
                <div class="result-status">
                    <div class="result-status-title">
                        <span class="result-status-icon">{alert_icon}</span>
                        {alert_msg}
                    </div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Result</div>
                        <div class="metric-value">{prediction.capitalize()}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value">{confidence_pct:.1f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Jitter</div>
                        <div class="metric-value">{jitter_val:.4f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Shimmer</div>
                        <div class="metric-value">{shimmer_val:.4f}</div>
                    </div>
                </div>
                
                <div class="visualization-section">
                    <h3>Voice Characteristics</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">HNR (dB)</div>
                            <div class="metric-value">{hnr_val:.2f}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">F0 Mean (Hz)</div>
                            <div class="metric-value">{f0_mean:.1f}</div>
                        </div>
                    </div>
                </div>
                
                <div class="visualization-section">
                    <h3>Audio Visualizations</h3>
                    <div class="images-row">
                        <div class="image-box">
                            <img src="/file={waveform_path}" alt="Waveform Visualization">
                            <div class="image-label">Waveform</div>
                        </div>
                        <div class="image-box">
                            <img src="/file={spectrogram_path}" alt="Spectrogram Visualization">
                            <div class="image-label">Spectrogram</div>
                        </div>
                    </div>
                </div>
                
                <div class="info-box">
                    <strong>Note:</strong> This analysis is for informational purposes only. Always consult with a qualified healthcare professional for medical diagnosis and treatment.
                </div>
            </div>
        </div>
        """
        return result
    except Exception as e:
        return f"""
        <div class="result-content" style="background: #FFEBEE; border: 1px solid #EF5350; border-radius: 6px; padding: 16px; color: #C62828;">
            <strong>Analysis Error:</strong> {str(e)}
        </div>
        """


def get_disease_info():
    """Return disease information"""
    return {
        "parkinsons": {
            "name": "Parkinson's Disease",
            "description": "Progressive nervous system disorder affecting movement.",
            "symptoms": ["Tremor", "Slow movement", "Rigid muscles", "Balance issues"],
            "video_id": "H_F7OxMEz90",
            "color": "#E91E63"
        },
        "alzheimers": {
            "name": "Alzheimer's Disease",
            "description": "Progressive disorder causing brain cell degeneration.",
            "symptoms": ["Memory loss", "Confusion", "Behavior changes"],
            "video_id": "wfGqbN5VmLo",
            "color": "#3F51B5"
        },
        "huntingtons": {
            "name": "Huntington's Disease",
            "description": "Inherited disease causing nerve cell breakdown.",
            "symptoms": ["Jerking movements", "Cognitive issues"],
            "video_id": "nJoS5MODfe0",
            "color": "#009688"
        }
    }


def create_app():
    """Create Gradio app with clean navigation"""
    initialize_database()
    session = load_session()
    
    # Shared CSS for modern SaaS design
    css = """
    * {
        box-sizing: border-box;
    }
    
    .gradio-container {
        max-width: 1400px;
        margin: auto;
        background: #FAFAFA;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        color: #333;
    }
    
    .gradio-container > div {
        padding: 0 !important;
    }
    
    .header {
        background: linear-gradient(135deg, #1976D2 0%, #0D47A1 100%);
        color: white;
        padding: 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(25, 118, 210, 0.15);
    }
    
    .header h1 {
        margin: 0;
        font-size: 36px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .header h2 {
        margin: 8px 0 0 0;
        font-size: 24px;
        font-weight: 500;
        opacity: 0.95;
    }
    
    .header p {
        margin: 8px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
        font-weight: 400;
    }
    
    .card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 12px 0;
        border: 1px solid #E0E0E0;
        transition: all 0.2s ease;
    }
    
    .card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }
    
    button[variant="primary"] {
        background: linear-gradient(135deg, #1976D2, #0D47A1) !important;
        color: white !important;
        padding: 12px 28px !important;
        border: none !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3) !important;
    }
    
    button[variant="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4) !important;
    }
    
    button[variant="primary"]:active {
        transform: translateY(0) !important;
    }
    
    button[variant="secondary"] {
        background: #2196F3 !important;
        color: white !important;
        padding: 10px 24px !important;
        border: none !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    button[variant="secondary"]:hover {
        background: #1976D2 !important;
        transform: translateY(-1px) !important;
    }
    
    .error {
        color: #C62828;
        background: #FFEBEE;
        padding: 16px;
        border-radius: 6px;
        margin: 12px 0;
        border-left: 4px solid #D32F2F;
        font-weight: 500;
    }
    
    .success {
        color: #2E7D32;
        background: #E8F5E9;
        padding: 16px;
        border-radius: 6px;
        margin: 12px 0;
        border-left: 4px solid #388E3C;
        font-weight: 500;
    }
    
    .info-section {
        background: #E3F2FD;
        border-left: 4px solid #1976D2;
        padding: 16px;
        border-radius: 6px;
        margin: 12px 0;
        color: #0D47A1;
        font-size: 14px;
    }
    
    .info-section strong {
        display: block;
        margin-bottom: 8px;
        font-size: 15px;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #1976D2;
        font-weight: 700;
    }
    
    input, textarea, select {
        border-radius: 6px !important;
        border: 1px solid #D0D0D0 !important;
        padding: 10px 12px !important;
        font-size: 14px !important;
    }
    
    input:focus, textarea:focus, select:focus {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1) !important;
    }
    
    .gradio-tabs {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .tab-button {
        border-bottom: 3px solid transparent !important;
        color: #666 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .tab-button.selected {
        color: #1976D2 !important;
        border-bottom-color: #1976D2 !important;
    }
    """
    
    with gr.Blocks(css=css, title="MediGuardian") as demo:
        # State for current page
        current_page = gr.State("login" if not session else "test")
        
        # Header
        gr.HTML("""
        <div class="header">
            <h1 style="margin: 0; font-size: 32px;">
                <span style="color: #4CAF50;">Medi</span>Guardian
            </h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Early Detection for Neurodegenerative Diseases</p>
        </div>
        """)
        
        # PAGE: LOGIN
        with gr.Group(visible=(not session)) as page_login:
            gr.Markdown("## Login to Your Account")
            login_components = login_form()
            login_btn = gr.Button("Login", variant="primary")
            login_msg = gr.HTML()
            register_btn = gr.Button("Create New Account")
            
            def do_login(username, password):
                success_msg = handle_login(username, password)
                if "Login successful" in str(success_msg):
                    return '<div class="success">Login successful! Redirecting...</div>'
                else:
                    return f'<div class="error">{success_msg}</div>'
            
            login_btn.click(
                fn=do_login,
                inputs=[login_components["username"], login_components["password"]],
                outputs=[login_msg]
            )
        
        # PAGE: REGISTER
        with gr.Group(visible=False) as page_register:
            gr.Markdown("## Create Your Account")
            register_components = register_form()
            register_btn_submit = gr.Button("Register", variant="primary")
            back_btn_login = gr.Button("Back to Login")
            register_msg = gr.HTML()
            
            def do_register(username, password, confirm, email, fname, lname, dob, phone, address):
                success_msg = handle_register(username, password, confirm, email, fname, lname, dob, phone, address)
                if "Registration successful" in str(success_msg):
                    return '<div class="success">Registration successful! Please log in.</div>'
                else:
                    return f'<div class="error">{success_msg}</div>'
            
            register_btn_submit.click(
                fn=do_register,
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
                outputs=[register_msg]
            )
            
            # Navigation: Register -> Login
            back_btn_login.click(
                fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
                outputs=[page_login, page_register]
            )
        
        # Navigation: Login -> Register
        register_btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            outputs=[page_login, page_register]
        )
        
        # PAGE: TEST (Public)
        with gr.Group(visible=(not session)) as page_test:
            gr.HTML('<div class="header"><h2 style="margin: 0;">Parkinson\'s Disease Voice Analysis</h2></div>')
            gr.Markdown("Upload or record a voice sample to analyze for Parkinson's disease indicators.")
            
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(type="filepath", label="Upload or Record Voice (.wav)")
                    analyze_btn = gr.Button("Analyze Voice", variant="primary")
                with gr.Column():
                    gr.Markdown("""
                    **Recording Guidelines:**
                    - Quiet environment with minimal noise
                    - Normal volume and pace
                    - At least 5 seconds of speech
                    - Sustained vowel sounds work best
                    - Keep microphone 6 inches away
                    """)
            
            result_output = gr.HTML()
            analyze_btn.click(fn=predict_parkinsons, inputs=[audio_input], outputs=[result_output])
        
        # PAGE: DASHBOARD (Logged in only)
        if session:
            with gr.Group(visible=True) as page_dashboard:
                gr.HTML(f'<div class="header"><h2 style="margin: 0;">Welcome, {session.get("first_name", "User")}! 👋</h2></div>')
                
                with gr.Tabs():
                    with gr.TabItem("Quick Test"):
                        audio_dash = gr.Audio(type="filepath", label="Upload or Record Voice")
                        analyze_dash_btn = gr.Button("Analyze", variant="primary")
                        result_dash = gr.HTML()
                        analyze_dash_btn.click(fn=predict_parkinsons, inputs=[audio_dash], outputs=[result_dash])
                    
                    with gr.TabItem("Information"):
                        diseases = get_disease_info()
                        for disease_id, disease in diseases.items():
                            with gr.Group():
                                gr.Markdown(f"### {disease['name']}\n{disease['description']}")
                                gr.Markdown(f"**Symptoms:** {', '.join(disease['symptoms'])}")
                
                    with gr.TabItem("Settings"):
                        gr.Markdown(f"**Username:** {session.get('username', 'N/A')}")
                        gr.Markdown(f"**Email:** {session.get('email', 'N/A')}")
                        logout_btn = gr.Button("Logout", variant="secondary")
                        
                        def do_logout():
                            clear_session()
                            return "Logged out successfully."
                        
                        logout_btn.click(fn=do_logout)
        
        # Public Navigation
        if not session:
            with gr.Row():
                test_nav_btn = gr.Button("Test Now", scale=1)
                login_nav_btn = gr.Button("Login", scale=1)
                
                test_nav_btn.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
                    outputs=[page_login, page_test]
                )
                login_nav_btn.click(
                    fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
                    outputs=[page_login, page_test]
                )
    
    return demo


if __name__ == "__main__":
    app = create_app()
    # share=True creates a public sharable link; server_name="0.0.0.0" allows LAN access from mobile
    app.launch(share=True, server_name="0.0.0.0")

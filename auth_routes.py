import gradio as gr
import os
import json
from functools import wraps
from db_utils import (register_user, authenticate_user, add_emergency_contact,
                    get_user_emergency_contacts, get_user_test_history)

# Session management
SESSION_FILE = "temp/session.json"
os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)

def save_session(user_data):
    """Save user session data to file"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(user_data, f)

def load_session():
    """Load user session data from file"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def clear_session():
    """Clear user session data"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def login_required(func):
    """Decorator to ensure user is logged in"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = load_session()
        if not session or 'id' not in session:
            return "Please log in to access this feature"
        return func(*args, **kwargs)
    return wrapper

def login_form():
    """Create login form elements"""
    with gr.Row():
        with gr.Column():
            username = gr.Textbox(label="Username")
            password = gr.Textbox(label="Password", type="password")
            login_button = gr.Button("Login")
            login_message = gr.HTML()
            
    with gr.Row():
        register_link = gr.Button("Create New Account")
    
    return {
        "username": username,
        "password": password,
        "login_button": login_button,
        "login_message": login_message,
        "register_link": register_link
    }

def register_form():
    """Create registration form elements"""
    with gr.Row():
        with gr.Column():
            username = gr.Textbox(label="Username*")
            password = gr.Textbox(label="Password*", type="password")
            confirm_password = gr.Textbox(label="Confirm Password*", type="password")
            email = gr.Textbox(label="Email*")
        
        with gr.Column():
            first_name = gr.Textbox(label="First Name*")
            last_name = gr.Textbox(label="Last Name*")
            dob = gr.Textbox(label="Date of Birth (YYYY-MM-DD)")
            phone = gr.Textbox(label="Phone Number")
            
    with gr.Row():
        address = gr.Textbox(label="Address", lines=2)
    
    with gr.Row():
        register_button = gr.Button("Register")
        back_button = gr.Button("Back to Login")
    
    register_message = gr.HTML()
    
    return {
        "username": username,
        "password": password,
        "confirm_password": confirm_password,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "dob": dob,
        "phone": phone,
        "address": address,
        "register_button": register_button,
        "back_button": back_button,
        "register_message": register_message
    }

def emergency_contact_form():
    """Create emergency contact form elements"""
    with gr.Row():
        with gr.Column():
            name = gr.Textbox(label="Contact Name*")
            relationship = gr.Textbox(label="Relationship*")
        
        with gr.Column():
            phone = gr.Textbox(label="Phone Number*")
            email = gr.Textbox(label="Email")
    
    with gr.Row():
        is_primary = gr.Checkbox(label="Set as Primary Emergency Contact")
        add_button = gr.Button("Add Contact")
    
    contact_message = gr.HTML()
    contact_list = gr.HTML()
    
    return {
        "name": name,
        "relationship": relationship,
        "phone": phone,
        "email": email,
        "is_primary": is_primary,
        "add_button": add_button,
        "contact_message": contact_message,
        "contact_list": contact_list
    }

def handle_login(username, password):
    """Handle login form submission"""
    success, result = authenticate_user(username, password)
    if success:
        user_data = result
        save_session(user_data)
        return f"""
        <div style="color: green; padding: 10px; background-color: #e8f5e9; border-radius: 5px;">
            Login successful! Welcome, {user_data['first_name']}!
            <script>
                setTimeout(function() {{
                    window.location.href = "?__theme=light";  // Reload page to trigger dashboard display
                }}, 1000);
            </script>
        </div>
        """
    else:
        return f"""
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            {result}
        </div>
        """

def handle_register(username, password, confirm_password, email, first_name, last_name, dob, phone, address):
    """Handle registration form submission"""
    # Basic validation
    if not username or not password or not email or not first_name or not last_name:
        return """
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Please fill in all required fields (marked with *).
        </div>
        """
    
    if password != confirm_password:
        return """
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Passwords do not match.
        </div>
        """
    
    success, result = register_user(username, password, email, first_name, last_name, dob, phone, address)
    if success:
        return f"""
        <div style="color: green; padding: 10px; background-color: #e8f5e9; border-radius: 5px;">
            Registration successful! You can now log in.
            <script>
                setTimeout(function() {{
                    window.location.href = "?__theme=light&page=login";
                }}, 1000);
            </script>
        </div>
        """
    else:
        return f"""
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Registration failed: {result}
        </div>
        """

def handle_logout():
    """Handle logout"""
    clear_session()
    return """
    <div style="color: green; padding: 10px; background-color: #e8f5e9; border-radius: 5px;">
        You have been logged out successfully.
        <script>
            setTimeout(function() {
                window.location.href = "?__theme=light";
            }, 1000);
        </script>
    </div>
    """

def handle_add_emergency_contact(name, relationship, phone, email, is_primary):
    """Handle adding an emergency contact"""
    # Basic validation
    if not name or not relationship or not phone:
        return """
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Please fill in all required fields (marked with *).
        </div>
        """, None
    
    session = load_session()
    if not session or 'id' not in session:
        return """
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Please log in to add emergency contacts.
        </div>
        """, None
    
    success, result = add_emergency_contact(
        session['id'], name, relationship, phone, email, is_primary
    )
    
    if success:
        message = """
        <div style="color: green; padding: 10px; background-color: #e8f5e9; border-radius: 5px;">
            Emergency contact added successfully.
        </div>
        """
        # Refresh contact list
        _, contacts = get_user_emergency_contacts(session['id'])
        contacts_html = render_emergency_contacts(contacts)
        return message, contacts_html
    else:
        return f"""
        <div style="color: red; padding: 10px; background-color: #ffebee; border-radius: 5px;">
            Failed to add emergency contact: {result}
        </div>
        """, None

def render_emergency_contacts(contacts):
    """Render emergency contacts as HTML"""
    if not contacts:
        return """
        <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
            No emergency contacts added yet.
        </div>
        """
    
    html = """
    <div style="padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
        <h3>Your Emergency Contacts</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #e0e0e0;">
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Name</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Relationship</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Phone</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Email</th>
                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Primary</th>
            </tr>
    """
    
    for contact in contacts:
        primary = "✓" if contact['is_primary'] else ""
        html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{contact['name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{contact['relationship']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{contact['phone_number']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{contact.get('email', '')}</td>
            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">{primary}</td>
        </tr>
        """
    
    html += """
        </table>
    </div>
    """
    return html
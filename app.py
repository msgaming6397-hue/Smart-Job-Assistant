import os
import json
import requests
import logging # Added logging
import tempfile # For safe temp dirs
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import PyPDF2
import docx
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Setup Logging (Visible in Render Logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google Gemini
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_warning_change_me_in_prod')

# Use system temp directory for uploads to avoid permission errors
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir() 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Fail-Safe Database Setup
DB_AVAILABLE = True
try:
    default_db_path = os.path.join(tempfile.gettempdir(), 'users.db')
    db_url = os.getenv('DATABASE_URL', f'sqlite:///{default_db_path}')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    # User Model (Must be defined before creation)
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(150), unique=True, nullable=False)
        password = db.Column(db.String(150), nullable=False)

    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully.")
        
except Exception as e:
    logger.error(f"DATABASE FAILURE: {e}. Switching to DEMO MODE.")
    DB_AVAILABLE = False
    # Create a dummy User class for demo mode
    class User(UserMixin):
        def __init__(self, id, username, password):
            self.id = id
            self.username = username
            self.password = password

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Demo User for Fallback
DEMO_USER = User(id=1, username="demo", password=generate_password_hash("demo"))

@login_manager.user_loader
def load_user(user_id):
    if DB_AVAILABLE:
        try:
            return User.query.get(int(user_id))
        except:
            return DEMO_USER if int(user_id) == 1 else None
    else:
        return DEMO_USER if int(user_id) == 1 else None

# ... (rest of imports)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
        except Exception as e:
            logger.error(f"Login Error: {e}")
            flash("System Error: Could not connect to database. Please check logs.")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        try:
            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists')
                return redirect(url_for('register'))
            
            # Use default hashing method (compatible with all versions)
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Register Error: {e}")
            flash(f"Error creating account: {str(e)}")
            return redirect(url_for('register'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/enhance')
def enhance_page():
    return render_template('enhance.html')



@app.route('/interview')
def interview_page():
    return render_template('interview.html')

@app.route('/roadmap')
def roadmap_page():
    return render_template('roadmap.html')

@app.route('/generate-interview', methods=['POST'])
def generate_interview():
    # Check if text input (role) or file upload
    if 'resume' in request.files:
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            text = ""
            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            elif filename.endswith('.docx'):
                text = extract_text_from_docx(filepath)
            
            # Context is resume text
            context_prompt = f"Resume Content:\n{text[:4000]}"
            
            try:
                os.remove(filepath)
            except: pass
    else:
        # Fallback manual role input (if we want to keep it, or just replace behavior)
        data = request.form
        role = data.get('role')
        context_prompt = f"Target Role: {role}"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return jsonify({"error": "No API Key"}), 500

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        You are an expert Interviewer. Based on the following candidate context, generate 5 relevant interview questions.
        
        {context_prompt}

        Include a mix of Technical, Behavioral, and Project-specific questions based on the resume/role.
        For each, provide a sample "Best Answer".
        
        Return ONLY a JSON list:
        [
            {{"type": "Technical/Behavioral", "question": "...", "answer": "..."}},
            ...
        ]
        """
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
        return jsonify({"questions": json.loads(text)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-roadmap', methods=['POST'])
def generate_roadmap():
    data = request.json
    current_role = data.get('current_role')
    target_role = data.get('target_role')

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return jsonify({"error": "No API Key"}), 500

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Create a 5-step Career Roadmap to go from {current_role} to {target_role}.
        Return ONLY a JSON list of steps:
        [
            {{"step": "Step 1 Title", "description": "Details..."}},
            ...
        ]
        """
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
        return jsonify({"roadmap": json.loads(text)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract Text
        text = ""
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(filepath)
            
        if not text.strip():
            return jsonify({"error": "Could not extract text from file."}), 400
            
        # Analyze
        analysis = analyze_with_ai(text)
        
        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass
            
        return jsonify(analysis)
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/enhance-cv', methods=['POST'])
def enhance_cv():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        text = ""
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(filepath)
            
        # Enhance
        suggestions = enhance_cv_with_ai(text)
        
        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass
            
        return jsonify({"suggestions": suggestions})
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    data = request.json
    name = data.get('name', 'Candidate')
    role = data.get('role', 'Job Applicant')
    skills = data.get('skills', [])
    
    if isinstance(skills, list):
        skills = ", ".join(skills)
        
    cover_letter = generate_cover_letter_ai(name, role, skills)
    return jsonify({"cover_letter": cover_letter})

@app.route('/loaders')
def loaders():
    return render_template('loaders.html')

@app.route('/backgrounds')
def backgrounds():
    return render_template('backgrounds.html')

@app.route('/generate-profile-summary', methods=['POST'])
def generate_profile_summary():
    data = request.json
    role = data.get('role', 'Professional')
    skills = data.get('skills', '')
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return jsonify({"error": "No API Key"}), 500

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Write a concise, professional resume summary (3-4 sentences) for a {role}.
        Highlight these key skills: {skills}.
        The tone should be confident and suitable for a resume header.
        """
        response = model.generate_content(prompt)
        return jsonify({"summary": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cv-templates')
def cv_templates():
    return render_template('templates_gallery.html')

@app.route('/parse-resume', methods=['POST'])
def parse_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        text = ""
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(filepath)
            
        # Parse with AI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: return jsonify({"error": "No API Key"}), 500

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            You are a Resume Parser. Extract data from the resume text below and structure it EXATLY as this JSON.
            
            Resume Text:
            {text[:4000]}

            Required JSON Structure:
            {{
                "personal": {{
                    "name": "Full Name",
                    "role": "Current Job Title",
                    "email": "Email",
                    "phone": "Phone",
                    "location": "City, Country",
                    "link": "LinkedIn/Portfolio URL",
                    "summary": "Professional Summary"
                }},
                "experience": [
                    {{ "company": "Company Name", "role": "Job Title", "start": "Start Date", "end": "End Date", "description": "Job Description" }}
                ],
                "education": [
                    {{ "school": "University Name", "degree": "Degree", "year": "Graduation Year" }}
                ],
                "skills": ["Skill 1", "Skill 2"]
            }}
            
            Return ONLY raw JSON. No markdown.
            """
            response = model.generate_content(prompt)
            content = response.text
             # Clean up JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed_data = json.loads(content)
            
            # Cleanup
            try: os.remove(filepath)
            except: pass
            
            return jsonify(parsed_data)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)

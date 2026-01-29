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
# Import helpers
from ai_helpers import extract_text_from_pdf, extract_text_from_docx, analyze_with_ai, generate_cover_letter_ai, enhance_cv_with_ai, generate_interview_ai, generate_roadmap_ai, generate_summary_ai, parse_resume_ai

# Setup Logging (Visible in Render Logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google Gemini
# import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    # genai.configure(api_key=api_key)
    pass

app = Flask(__name__)
# ... (Environment loading)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_warning_change_me_in_prod')

# Use system temp directory for uploads
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir() 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ... (routes)

@app.route('/')
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

    if not api_key: return jsonify({"error": "No API Key"}), 500

    questions = generate_interview_ai(context_prompt)
    return jsonify({"questions": questions})

@app.route('/generate-roadmap', methods=['POST'])
def generate_roadmap():
    data = request.json
    current_role = data.get('current_role')
    target_role = data.get('target_role')

    if not api_key: return jsonify({"error": "No API Key"}), 500

    roadmap = generate_roadmap_ai(current_role, target_role)
    return jsonify({"roadmap": roadmap})

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
    
    if not api_key: return jsonify({"error": "No API Key"}), 500

    summary = generate_summary_ai(role, skills)
    return jsonify({"summary": summary})

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

        parsed_data = parse_resume_ai(text)
        
        # Cleanup
        try: os.remove(filepath)
        except: pass
        
        return jsonify(parsed_data)
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)

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

# Database Configuration
db_url = os.getenv('DATABASE_URL', 'sqlite:///users.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure tables exist (Run this at startup)
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# (No need to os.makedirs for tempfile.gettempdir() as it exists)


# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return text

def analyze_with_ai(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Missing GEMINI_API_KEY in .env file."}

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) scanner and career coach. Analyze the resume text below.
        
        Resume Text:
        {text[:4000]}

        Tasks:
        1. Extract specific Technical Skills (programming, tools, hard skills).
        2. Extract specific Soft Skills (communication, leadership, etc.).
        3. Suggest 3 suitable job roles containing a title and description.
        4. Calculate an estimated ATS Score (0-100).
        5. Provide 3 specific tips to improve the resume.
        6. Identify 3 critical MISSING skills for the suggested roles and provide a brief recommendation on how to verify/learn them.

        Return ONLY a JSON object with this structure (no markdown formatting):
        {{
            "technical_skills": ["Tech Skill 1", "Tech Skill 2", ...],
            "soft_skills": ["Soft Skill 1", "Soft Skill 2", ...],
            "job_roles": [
                {{"title": "Role 1", "description": "Why this fits..."}},
                {{"title": "Role 2", "description": "Why this fits..."}},
                {{"title": "Role 3", "description": "Why this fits..."}}
            ],
            "ats_score": 0,
            "ats_tips": ["Tip 1", "Tip 2", "Tip 3"],
            "missing_skills": [
                {{"skill": "Missing Skill 1", "recommendation": "Take a course on..."}},
                {{"skill": "Missing Skill 2", "recommendation": "Build a project using..."}}
            ]
        }}
        """
        
        response = model.generate_content(prompt)
        content = response.text
        
        # Clean up JSON if model adds backticks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
        
    except Exception as e:
        # Fallback for errors
        return {"error": f"AI Error: {str(e)}"}

def generate_cover_letter_ai(name, role, skills):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: API Key not found."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Write a professional and persuasive cover letter for:
        Candidate Name: {name}
        Target Job Role: {role}
        Key Skills: {skills}

        The tone should be enthusiastic, professional, and confident.
        Keep it concise (under 300 words).
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"

def enhance_cv_with_ai(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "<p>Error: API Key not found.</p>"

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a professional Top-Tier Resume Writer and Career Coach. Review the resume text below and provide a detailed critique to ENHANCE it.
        
        Resume Text:
        {text[:4000]}

        Focus on:
        1. **Impact & Clarity**: Are bullet points result-oriented? (e.g., "Increased sales by 20%" vs "Responsible for sales")
        2. **Structure & Formatting**: Is the layout logical? (Note: you are reading text, so infer structure from flow)
        3. **Language**: Use of strong action verbs.
        4. **Missing Content**: What important sections are missing? (Projects, Certifications, etc.)

        Output Format:
        Return a structured HTML string (NOT Markdown, NOT JSON). Use <h3> for headings, <ul> and <li> for points, and <strong> for emphasis.
        Do NOT include <html> or <body> tags. Just the content div.
        Example:
        <h3>1. Impact Analysis</h3>
        <ul><li>...</li></ul>
        """
        
        response = model.generate_content(prompt)
        content = response.text
        # Cleanup markdown code blocks if present
        content = content.replace("```html", "").replace("```", "").strip()
        return content
    except Exception as e:
        return f"<p>Error generating suggestions: {str(e)}</p>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
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

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
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

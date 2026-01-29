import os
import json
import requests
import PyPDF2
import docx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

def call_gemini(text):
    if not API_KEY: return "Error: No API Key found in .env"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": text}]}]}
    try:
        resp = requests.post(f"{URL}?key={API_KEY}", headers=headers, json=data, timeout=30)
        
        # Check for 400/403/404 explicitly
        if resp.status_code != 200:
            return f"Error {resp.status_code}: {resp.text}"
            
        res_json = resp.json()
        if 'candidates' not in res_json or not res_json['candidates']:
            return "Error: No response candidates (Possible Safety Block)."
            
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

# Extractors
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

# AI Functions
def analyze_with_ai(text):
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
    Return ONLY a JSON object with this structure:
    {{
        "technical_skills": [], "soft_skills": [],
        "job_roles": [{{"title": "", "description": ""}}],
        "ats_score": 0, "ats_tips": [],
        "missing_skills": [{{"skill": "", "recommendation": ""}}]
    }}
    """
    res = call_gemini(prompt)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0]
        elif "```" in res: res = res.split("```")[1].split("```")[0]
        return json.loads(res.strip())
    except:
        return {"error": f"Failed to parse AI response: {res}"}

def generate_cover_letter_ai(name, role, skills):
    prompt = f"Write a professional, 300-word cover letter for {name}, applying for {role}, with skills: {skills}."
    return call_gemini(prompt)

def enhance_cv_with_ai(text):
    prompt = f"""
    Review this resume and provide enhancement suggestions as Structured HTML (Use <h3>, <ul>, <li> tags ONLY). 
    Focus on Impact, Clarity, and Missing Content.
    Resume: {text[:4000]}
    """
    res = call_gemini(prompt)
    return res.replace("```html", "").replace("```", "")

def generate_interview_ai(context):
    prompt = f"""
    Generate 5 interview questions based on the following context:
    {context[:4000]}
    Include a mix of Technical and Behavioral. Provide a sample "Best Answer" for each.
    Return ONLY a JSON list:
    [{{"type": "Technical/Behavioral", "question": "...", "answer": "..."}}]
    """
    res = call_gemini(prompt)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0]
        elif "```" in res: res = res.split("```")[1].split("```")[0]
        return json.loads(res.strip())
    except:
        return [{"type": "Error", "question": "Failed to generate", "answer": res}]

def generate_roadmap_ai(current, target):
    prompt = f"""
    Create a 5-step Career Roadmap to go from {current} to {target}.
    Return ONLY a JSON list:
    [{{"step": "Step Title", "description": "Detailed description..."}}]
    """
    res = call_gemini(prompt)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0]
        elif "```" in res: res = res.split("```")[1].split("```")[0]
        return json.loads(res.strip())
    except:
        return [{"step": "Error", "description": res}]

def generate_summary_ai(role, skills):
    prompt = f"Write a concise, professional resume summary (3-4 sentences) for a {role} with skills: {skills}."
    return call_gemini(prompt)

def parse_resume_ai(text):
    prompt = f"""
    Extract resume data to JSON.
    resume: {text[:4000]}
    Structure:
    {{ "personal": {{ "name": "", "email": "", "mobile": "", "linkedin": "", "summary": "" }}, 
      "experience": [], "education": [], "skills": [] }}
    Return ONLY JSON.
    """
    res = call_gemini(prompt)
    try:
        if "```json" in res: res = res.split("```json")[1].split("```")[0]
        elif "```" in res: res = res.split("```")[1].split("```")[0]
        return json.loads(res.strip())
    except:
        return {"error": res}

import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="Silvia Pagliarini Portfolio", page_icon="💼", layout="wide")

# 2. Sidebar Navigation & Contact Info
with st.sidebar:
    st.title("Contact Info")
    st.image("https://placeholder.com", width=150)
    
    # 🔗 LINK YOUR LINKEDIN HERE:
    st.markdown("### 🔗 [Connect on LinkedIn](https://www.linkedin.com/in/silviapagliarini/)")
    
    st.markdown("---")
    st.caption("🤖 Powered by an automated Python Git-Parsing Agent.")

# 3. Securely Load Your Gemini API Key from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = os.getenv("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)

# 4. Smart Caching: Watch the file's modification timestamp
# Streamlit will ONLY run this function if the timestamp of cv.pdf changes!
@st.cache_data
def compile_portfolio_from_repo(pdf_filename, file_timestamp):
    # Fallback default data if things fail or key is missing
    default_data = {
        "name": "Silvia Pagliarini",
        "tagline": "Senior Product Engineer | Generative AI & Agentic Systems | PhD Computer Science",
        "summary": "summary",
        "skills": ["Python", "Git"],
        "experience": []
    }
    
    if not api_key:
        return default_data
        
    try:
        # Read the local cv.pdf cloned from your repository
        reader = PdfReader(pdf_filename)
        raw_text = ""
        for page in reader.pages:
            raw_text += page.extract_text()
        
        # Initialize the AI Client
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an expert resume parsing agent. Analyze the following raw text from a CV/Resume. 
        Extract the details into a clean, valid JSON format matching this schema exactly. 
        Do not include any conversational text, markdown formatting, or code fences (no ```json). 
        Only output the raw JSON object string.

        JSON Schema Expected:
        {{
            "summary": "A concise executive summary paragraph based on their profile",
            "skills": ["Skill1", "Skill2", "Skill3", "Skill4"],
            "work_experience": [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "dates": "Years/Dates active",
                    "bullets": ["Achievement 1", "Achievement 2"]
                }}
            "education": [
                {{
                    "degree": "Degree Name",
                    "institution": "Institution Name",
                    "dates": "Years/Dates attended"
                }}
            ]
        }}

        Raw Resume Text:
        {raw_text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return json.loads(response.text.strip())
    except Exception as e:
        return default_data

# 5. Check the exact timestamp of cv.pdf right now
pdf_path = "cv.pdf"
if os.path.exists(pdf_path):
    current_timestamp = os.path.getmtime(pdf_path)
else:
    current_timestamp = 0.0

# Pass the timestamp into the function. If it matches the cached run, the function skips entirely!
data = compile_portfolio_from_repo(pdf_path, current_timestamp)

# 6. Render the Beautiful Main Portfolio Page Layout
st.title(f"{data['name']}")
st.subheader(data['tagline'])

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📝 About Me")
    st.write(data['summary'])
    
    st.markdown("---")
    st.markdown("### 💼 Work History")
    if not data['experience']:
        st.info("No work history found. Ensure cv.pdf is in your repo and API Key is added to settings.")
    else:
        for job in data['experience']:
            with st.expander(f"{job['title']} — {job['company']} ({job['dates']})", expanded=True):
                for bullet in job['bullets']:
                    st.markdown(f"- {bullet}")
        for edu in data.get('education', []):
            with st.expander(f"{edu['degree']} — {edu['institution']} ({edu['dates']})", expanded=True):
                st.markdown(f"- {edu['degree']} from {edu['institution']} ({edu['dates']})")

with col2:    
    st.markdown("### 🛠️ Core Competencies")
    for skill in data['skills']:
        st.button(skill, disabled=True, key=f"btn_{skill}")

import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_CACHE_PATH = BASE_DIR / "parsed_cv.json"

DEFAULT_DATA = {
    "name": "Silvia Pagliarini",
    "tagline": "Senior Product Engineer | Generative AI & Agentic Systems | PhD Computer Science",
    "summary": "Upload or add your cv.pdf to compile your executive profile.",
    "skills": ["Python", "Git", "Generative AI", "Agentic Systems"],
    "work_experience": []
}

# 1. Page Configuration
st.set_page_config(page_title="Silvia Pagliarini Portfolio", page_icon="💼", layout="wide")

# Initialize persistent session state so background re-runs look at local memory first
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = None

# 2. Sidebar Navigation & Contact Info
with st.sidebar:
    st.title("Contact Info")
    profile_pic = BASE_DIR / "profile_pic.jpg"
    if profile_pic.exists():
        st.image(str(profile_pic), width=150)
    else:
        st.image("https://placehold.co/150x150.png", width=150)
    
    st.markdown("### 🔗 [Connect on LinkedIn](https://www.linkedin.com/in/silviapagliarini/)")
    st.markdown("---")
    st.caption("🤖 Powered by an automated Python Git-Parsing Agent.")

# 3. Securely Load Your Gemini API Key from Streamlit Secrets
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"⚠️ Gemini configuration failed: {e}")

# 4. Heavy Compilation Function (Only triggers if cache files are missing)
def compile_portfolio_from_repo(pdf_filename):
    if not api_key:
        return DEFAULT_DATA, "Missing GEMINI_API_KEY"

    pdf_path = Path(pdf_filename)
    if not pdf_path.exists():
        return DEFAULT_DATA, f"CV file not found: {pdf_path}"

    try:
        reader = PdfReader(str(pdf_path))
        raw_text = ""
        for page in reader.pages:
            text = page.extract_text() or ""
            raw_text += text

        model = genai.GenerativeModel("gemini-3.8-flash")

        prompt = f"""
        You are an expert resume parsing agent. Analyze the following raw text from a CV/Resume.
        Extract the details into a clean, valid JSON format matching this schema exactly.
        Do not include any conversational text, markdown formatting, or code fences (no ```json).
        Only output the raw JSON object string.

        JSON Schema Expected:
        {{
            "name": "Full Name",
            "tagline": "A punchy, professional title/headline",
            "summary": "A concise executive summary paragraph based on their profile",
            "skills": ["Skill1", "Skill2", "Skill3", "Skill4"],
            "work_experience": [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "dates": "Years/Dates active",
                    "bullets": ["Achievement 1", "Achievement 2"]
                }}
            ]
        }}

        Raw Resume Text:
        {raw_text}
        """

        response = model.generate_content(prompt)
        response_text = (getattr(response, "text", "") or "").strip()
        if response_text.startswith("```"):
            response_text = response_text.strip("`")
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].lstrip()

        payload = json.loads(response_text)
        payload.setdefault("name", DEFAULT_DATA["name"])
        payload.setdefault("tagline", DEFAULT_DATA["tagline"])
        payload.setdefault("summary", DEFAULT_DATA["summary"])
        payload.setdefault("skills", DEFAULT_DATA["skills"])
        payload.setdefault("work_experience", [])

        # Write out to a permanent local backup json file so the API is never hit again
        with open(JSON_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)

        return payload, None
    except Exception as e:
        return DEFAULT_DATA, str(e)

# 5. Smart Multi-Tier Cache Router
data = DEFAULT_DATA
parse_error = None
pdf_path = BASE_DIR / "cv.pdf"

# Tier 1: Look at current app interaction session state
if st.session_state.portfolio_data is not None:
    data = st.session_state.portfolio_data
# Tier 2: Check if a pre-compiled JSON file already exists on the repo filesystem
elif JSON_CACHE_PATH.exists():
    try:
        with open(JSON_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.portfolio_data = data
    except Exception as e:
        parse_error = f"Failed reading local file cache: {e}"
# Tier 3: If both are empty, execute the live API request exactly once
elif pdf_path.exists():
    data, parse_error = compile_portfolio_from_repo(str(pdf_path))
    if not parse_error:
        st.session_state.portfolio_data = data

# Notify user of alternative states in the sidebar safely
if parse_error:
    st.sidebar.error(f"⚠️ Portfolio agent failed: {parse_error}")
    st.warning("Using fallback placeholder data because compilation step encountered an exception.")
elif JSON_CACHE_PATH.exists():
    st.sidebar.success("⚡ Data loaded instantly via local Git JSON-cache.")

# 6. Render Layout Structure
st.title(f"{data['name']}")
st.subheader(data['tagline'])

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📝 About Me")
    st.write(data['summary'])
    
    st.markdown("---")
    st.markdown("### 💼 Work History")
    if not data['work_experience']:
        st.info("No work history layout resolved. Verify structural array parameters.")
    else:
        for job in data['work_experience']:
            with st.expander(f"**{job['title']}** — {job['company']} ({job['dates']})", expanded=True):
                for bullet in job['bullets']:
                    st.markdown(f"- {bullet}")
                    
        for edu in data.get('education', []):
            with st.expander(f"**{edu['degree']}** — {edu['institution']} ({edu['dates']})", expanded=True):
                st.markdown(f"- Completed specialization criteria.")

with col2:    
    st.markdown("### 🛠️ Core Competencies")
    # Clean styling wrap for interactive button chips
    for skill in data['skills']:
        st.button(skill, disabled=True, key=f"btn_{skill}")
        
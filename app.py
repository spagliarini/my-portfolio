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

    st.markdown(
        """
        <a href="https://www.linkedin.com/in/silviapagliarini/" target="_blank"
           rel="noopener noreferrer" aria-label="Connect on LinkedIn"
           style="display:inline-flex;align-items:center;gap:8px;padding:8px 14px;
                  background:#0a66c2;color:white;text-decoration:none;border-radius:6px;
                  font-weight:600;">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
               viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853
            0-2.136 1.445-2.136 2.939v5.667H9.35V9h3.414v1.561h.049c.476-.9
            1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286ZM5.337
            7.433a2.062 2.062 0 1 1 0-4.124 2.062 2.062 0 0 1 0 4.124Zm1.782
            13.019H3.555V9h3.564v11.452ZM22.225 0H1.771C.792 0 0 .774 0
            1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227
            24 22.271V1.729C24 .774 23.2 0 22.222 0h.003Z"/>
          </svg>
          <span>Connect on LinkedIn</span>
        </a>
        """,
        unsafe_allow_html=True,
    )
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

        model = genai.GenerativeModel("gemini-3.5-flash-lite")

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
        
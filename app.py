import streamlit as st
from pypdf import PdfReader
import google.genai as genai
import json

# Page config
st.set_page_config(page_title="My AI-Compiled Portfolio", page_icon="💼", layout="wide")

# Initialize session state so the site remembers your data after it parses
if "profile_data" not in st.session_state:
    st.session_state.profile_data = {
        "name": "Your Name",
        "tagline": "Your Professional Title",
        "summary": "Upload your resume in the sidebar to populate this automatically!",
        "skills": ["Python", "Data Analysis"],
        "experience": []
    }

# --- SIDEBAR: THE AI AGENT ---
with st.sidebar:
    st.title("🤖 Resume Agent")
    st.subheader("Compile Site via AI")
    
    # 1. API Key Input (Get a free one from Google AI Studio)
    api_key = st.text_input("Enter Gemini API Key:", type="password", help="Get a free key from Google AI Studio")
    st.markdown("[Get a Free Gemini API Key Key 🔗](https://google.com)")
    
    # 2. File Uploader
    uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    
    if uploaded_file and api_key:
        if st.button("🚀 Run AI Compiler"):
            with st.spinner("Agent is extracting information from your CV..."):
                try:
                    # Read the PDF text
                    reader = PdfReader(uploaded_file)
                    raw_text = ""
                    for page in reader.pages:
                        raw_text += page.extract_text()
                    
                    # Initialize Gemini Client
                    client = genai.Client(api_key=api_key)
                    
                    # Strict prompt instructing the agent to return ONLY raw JSON matching our structure
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
                        "experience": [
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
                    
                    # Call the AI model
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    # Parse the agent's output and update the page state
                    parsed_json = json.loads(response.text.strip())
                    st.session_state.profile_data = parsed_json
                    st.success("🎉 Portfolio compiled successfully!")
                    
                except Exception as e:
                    st.error(f"Error parsing resume: {e}")
                    st.info("Tip: Double-check your API key and ensure the PDF text is highlightable.")

    st.markdown("---")
    st.caption("Push changes to GitHub after checking layout.")

# --- MAIN CONTENT AREA: DISPLAY THE DYNAMIC PORTFOLIO ---
data = st.session_state.profile_data

st.title(f"👋 Welcome to the Portfolio of {data['name']}")
st.subheader(data['tagline'])

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 About Me")
    st.write(data['summary'])
    
    st.markdown("---")
    st.markdown("### 💼 Work History")
    if not data['experience']:
        st.info("No work history found yet. Upload a CV in the sidebar!")
    else:
        for job in data['experience']:
            with st.expander(f"{job['title']} at {job['company']} ({job['dates']})", expanded=True):
                for bullet in job['bullets']:
                    st.markdown(f"- {bullet}")

with col2:
    st.markdown("### 🛠️ Core Competencies")
    for skill in data['skills']:
        st.button(skill, disabled=True, key=f"btn_{skill}")

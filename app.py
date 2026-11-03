import html
import hmac
import json
import os
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "parsed_cv.json"
CV_PATH = BASE_DIR / "cv.pdf"


class ProfileGenerationError(Exception):
    pass


def get_secret(name):
    try:
        return st.secrets.get(name) or os.getenv(name)
    except StreamlitSecretNotFoundError:
        return os.getenv(name)


def generate_profile(api_key):
    import google.generativeai as genai
    from google.api_core.exceptions import GoogleAPIError
    from pypdf import PdfReader

    if not CV_PATH.exists():
        raise FileNotFoundError(f"CV file not found: {CV_PATH}")

    reader = PdfReader(str(CV_PATH))
    raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""
    You are an expert resume parsing agent. Extract the CV into a valid JSON object.
    Return only JSON, without markdown or conversational text, using this schema:
    {{
        "name": "Full Name",
        "tagline": "Professional headline",
        "current_position": "Current job title and company",
        "current_position_summary": "Concise summary of responsibilities and impact in the current role",
        "summary": "Concise professional summary",
        "skills": ["Skill"],
        "work_experience": [
            {{
                "title": "Job title",
                "company": "Company",
                "dates": "Dates",
                "bullets": ["Achievement"]
            }}
        ],
        "education": [
            {{
                "degree": "Degree",
                "institution": "Institution",
                "dates": "Dates",
                "bullets": ["Relevant detail"]
            }}
        ]
    }}

    CV text:
    {raw_text}
    """
    try:
        response = model.generate_content(prompt)
    except GoogleAPIError as error:
        raise ProfileGenerationError(f"Gemini profile generation failed: {error}") from error
    response_text = (getattr(response, "text", "") or "").strip()
    if response_text.startswith("```"):
        response_text = response_text.strip("`").strip()
        if response_text.lower().startswith("json"):
            response_text = response_text[4:].lstrip()

    profile = json.loads(response_text)
    if not isinstance(profile, dict):
        raise ValueError("The generated profile must be a JSON object.")

    defaults = {
        "name": "Silvia Pagliarini",
        "tagline": "",
        "current_position": "",
        "current_position_summary": "",
        "summary": "",
        "skills": [],
        "work_experience": [],
        "education": [],
    }
    for key, default in defaults.items():
        profile.setdefault(key, default)
    for key in (
        "name",
        "tagline",
        "current_position",
        "current_position_summary",
        "summary",
    ):
        if not isinstance(profile[key], str):
            raise ValueError(f'The generated profile field "{key}" must be text.')
    for key in ("skills", "work_experience", "education"):
        if not isinstance(profile[key], list):
            raise ValueError(f'The generated profile field "{key}" must be a list.')
    for job in profile["work_experience"]:
        if not isinstance(job, dict) or not all(
            isinstance(job.get(key), str) for key in ("title", "company", "dates")
        ):
            raise ValueError("Each work experience entry needs a title, company, and dates.")
        job.setdefault("bullets", [])
        if not isinstance(job["bullets"], list):
            raise ValueError("Work experience bullets must be a list.")
    for education in profile["education"]:
        if not isinstance(education, dict) or not all(
            isinstance(education.get(key), str)
            for key in ("degree", "institution", "dates")
        ):
            raise ValueError(
                "Each education entry needs a degree, institution, and dates."
            )
        education.setdefault("bullets", [])
        if not isinstance(education["bullets"], list):
            raise ValueError("Education bullets must be a list.")

    return profile


def save_profile(profile):
    temporary_path = PROFILE_PATH.with_suffix(".json.tmp")
    with temporary_path.open("w", encoding="utf-8") as profile_file:
        json.dump(profile, profile_file, indent=2, ensure_ascii=False)
        profile_file.write("\n")
    temporary_path.replace(PROFILE_PATH)

# 1. Page Configuration
st.set_page_config(page_title="Silvia Pagliarini Portfolio", page_icon="💼", layout="wide")

# 2. Sidebar Navigation & Contact Info
with st.sidebar:
    profile_pic = BASE_DIR / "profile_pic.jpg"
    if profile_pic.exists():
        st.image(str(profile_pic), width=150)
    else:
        st.image("https://placehold.co/150x150.png", width=150)

    page = st.radio(
        "Menu",
        ["Home", "Work Experience", "Education"],
    )
    st.markdown("---")
    st.title("Contact Info")

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
    st.caption("Profile content is maintained by Silvia.")
    refresh_password = get_secret("PROFILE_REFRESH_PASSWORD")
    if refresh_password:
        with st.expander("Owner: refresh profile from CV"):
            password = st.text_input(
                "Owner password",
                type="password",
                key="profile_refresh_password",
            )
            if st.button("Regenerate profile", key="regenerate_profile"):
                if not hmac.compare_digest(password, str(refresh_password)):
                    st.error("Incorrect owner password.")
                else:
                    api_key = get_secret("GEMINI_API_KEY")
                    if not api_key:
                        st.error("GEMINI_API_KEY is not configured.")
                    else:
                        try:
                            refreshed_profile = generate_profile(api_key)
                            save_profile(refreshed_profile)
                        except (
                            FileNotFoundError,
                            OSError,
                            ValueError,
                            json.JSONDecodeError,
                            ModuleNotFoundError,
                            ProfileGenerationError,
                        ) as error:
                            st.error(f"Profile refresh failed: {error}")
                        else:
                            st.session_state["refreshed_profile_json"] = json.dumps(
                                refreshed_profile,
                                indent=2,
                                ensure_ascii=False,
                            )
                            st.success("Profile regenerated and loaded for this app instance.")

            refreshed_json = st.session_state.get("refreshed_profile_json")
            if refreshed_json:
                st.download_button(
                    "Download refreshed profile JSON",
                    data=refreshed_json,
                    file_name="parsed_cv.json",
                    mime="application/json",
                )

# 3. Load the shared, maintainer-managed profile snapshot.
with PROFILE_PATH.open(encoding="utf-8") as profile_file:
    data = json.load(profile_file)

# 4. Render the selected page
st.title(f"{data['name']}")

if page == "Home":
    st.markdown("### 📝 About Me")
    st.write(data['summary'])

    st.markdown("---")
    st.markdown("### Current Position")
    current_position = data["current_position"]
    current_position_summary = data.get("current_position_summary", "")
    if not current_position:
        current_job = next(
            (
                job
                for job in data["work_experience"]
                if any(
                    marker in str(job.get("dates", "")).lower()
                    for marker in ("present", "current", "now")
                )
            ),
            None,
        )
        if current_job:
            current_position = (
                f"{current_job.get('title', '')} — {current_job.get('company', '')}"
            ).strip(" —")
            current_position_summary = current_position_summary or " ".join(
                current_job.get("bullets", [])
            )
        else:
            current_position = data["tagline"]
    st.write(current_position)
    if current_position_summary:
        st.write(current_position_summary)

    st.markdown("---")
    st.markdown("### 🛠️ Skills")
    skills = "".join(
        f'<span style="display:inline-block;padding:6px 12px;border-radius:16px;'
        f'background-color:var(--secondary-background-color);'
        f'color:var(--text-color);margin:0 8px 8px 0;">{html.escape(str(skill))}</span>'
        for skill in data["skills"]
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;align-items:center;">{skills}</div>',
        unsafe_allow_html=True,
    )

elif page == "Work Experience":
    st.markdown("### 💼 Work Experience")
    if not data['work_experience']:
        st.info("No work experience is available.")
    else:
        for job in data['work_experience']:
            with st.expander(f"**{job['title']}** — {job['company']} ({job['dates']})", expanded=True):
                for bullet in job.get('bullets', []):
                    st.markdown(f"- {bullet}")

elif page == "Education":
    st.markdown("### 🎓 Education")
    if not data['education']:
        st.info("No education history is available.")
    else:
        for edu in data['education']:
            with st.expander(
                f"**{edu.get('degree', 'Qualification')}** — "
                f"{edu.get('institution', 'Institution not specified')} "
                f"({edu.get('dates', 'Dates not specified')})",
                expanded=True,
            ):
                for bullet in edu.get('bullets', []):
                    st.markdown(f"- {bullet}")
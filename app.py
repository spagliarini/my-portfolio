import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="My Interactive Portfolio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Sidebar / Navigation
with st.sidebar:
    st.image("https://placeholder.com", caption="Your Name", width=150)
    st.title("Navigation")
    page = st.radio("Go to:", ["About Me", "Experience & Education", "Interactive Projects", "Contact"])
    
    st.markdown("---")
    st.markdown("🔗 **Connect with me:**")
    st.markdown("[LinkedIn](https://linkedin.com)")
    st.markdown("[GitHub](https://github.com)")

# 3. Page 1: About Me
if page == "About Me":
    st.title("👋 Welcome to My Portfolio")
    st.subheader("Your Professional Tagline / Role (e.g., Data Scientist | Full Stack Developer)")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Executive Summary
        Paste your LinkedIn 'About' section or CV summary here. 
        Highly motivated professional with experience in building data-driven applications, 
        solving complex problems, and scaling infrastructure.
        """)
    with col2:
        st.markdown("### Core Skills")
        skills = ["Python", "Streamlit", "Machine Learning", "SQL", "Git", "Project Management"]
        for skill in skills:
            st.button(skill, disabled=True, key=skill)

# 4. Page 2: Experience & Education
elif page == "Experience & Education":
    st.title("💼 Work History & Education")
    
    st.markdown("### 🚀 Work Experience")
    with st.expander("Senior Role Title — Company Name (2024 - Present)", expanded=True):
        st.caption("📍 Location | Full-time")
        st.markdown("""
        - **Achievement 1:** Accomplished X, measured by Y, by doing Z.
        - **Achievement 2:** Led a team of 4 to deploy a critical pipeline.
        """)
        
    with st.expander("Junior Role Title — Previous Company (2022 - 2024)"):
        st.caption("📍 Location | Remote")
        st.markdown("""
        - Developed and optimized Python scripts reducing runtime by 30%.
        - Collaborative team player across cross-functional squads.
        """)
        
    st.markdown("---")
    st.markdown("### 🎓 Education")
    st.markdown("**B.S. in Computer Science** — University Name *(Graduated 2022)*")

# 5. Page 3: Interactive Projects (The "AI Hook")
elif page == "Interactive Projects":
    st.title("🛠️ Interactive Project Showcase")
    st.write("Since this is built in Python, you can host actual live models or interactive data dashboards right here!")
    
    # Example interactive widget: A live mock ROI calculator or model simulator
    st.markdown("### Project Feature: Business ROI Calculator")
    st.write("Adjust the sliders below to see how my automation code saves company money in real time.")
    
    hours_saved = st.slider("Hours saved per week by automation:", 1, 40, 15)
    hourly_rate = st.slider("Average hourly employee rate ($):", 20, 150, 50)
    
    yearly_savings = hours_saved * hourly_rate * 52
    st.metric(label="Estimated Yearly Savings For Your Team", value=f"${yearly_savings:,}")

# 6. Page 4: Contact
elif page == "Contact":
    st.title("📬 Get In Touch")
    st.write("Feel free to reach out for collaborations or opportunities!")
    
    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email Address")
        message = st.text_area("Your Message")
        submit = st.form_submit_button("Send Message")
        
        if submit:
            st.success(f"Thank you {name}! Your message has been sent successfully.")
            
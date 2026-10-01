import streamlit as st
import requests
import time
import pandas as pd

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Taheel AI | تأهيل", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "package" not in st.session_state:
    st.session_state.package = None
if "processing" not in st.session_state:
    st.session_state.processing = False

st.title("🚀 Taheel AI (نظام التأهيل الذكي)")
st.markdown("**Enterprise 30-60-90 Day Employee Onboarding & Probation Governance Engine**")

tabs = st.tabs([
    "1. Setup & Upload", 
    "2. 30-60-90 Timeline", 
    "3. Daily Tasks", 
    "4. Manager Gates", 
    "5. Export Center"
])

# --- TAB 1: SETUP & UPLOAD ---
with tabs[0]:
    st.header("Create New Onboarding Profile")
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", "RiyadhPay Fintech")
        department = st.text_input("Department", "Customer Operations")
        role_title = st.text_input("Role Title", "Customer Support Specialist")
    with col2:
        mentor_name = st.text_input("Manager / Mentor Name", "Sarah Al-Saud")
        language = st.selectbox("Language", ["English (en)", "Arabic (ar)"])
        lang_code = "en" if "en" in language else "ar"
        
    st.markdown("---")
    st.subheader("Upload Company Manual (SOPs)")
    uploaded_file = st.file_uploader("Upload PDF or Markdown Manual", type=["pdf", "md", "txt"])
    
    if st.button("Generate Onboarding Pipeline", type="primary") and uploaded_file:
        st.session_state.processing = True
        
        # 1. Start Job
        files = {"document": (uploaded_file.name, uploaded_file, "application/octet-stream")}
        data = {
            "company_name": company_name,
            "department": department,
            "role_title": role_title,
            "mentor_name": mentor_name,
            "language": lang_code
        }
        
        try:
            res = requests.post(f"{API_URL}/jobs", files=files, data=data)
            if res.status_code == 200:
                job_data = res.json()
                st.session_state.job_id = job_data["job_id"]
                st.success("Job started successfully!")
            else:
                st.error(f"Failed to start job: {res.text}")
                st.session_state.processing = False
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Is FastAPI running on port 8000? (uvicorn src.taheel.api.main:app --reload)")
            st.session_state.processing = False

    # Polling logic
    if st.session_state.job_id and st.session_state.processing:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while st.session_state.processing:
            try:
                res = requests.get(f"{API_URL}/jobs/{st.session_state.job_id}")
                if res.status_code == 200:
                    job = res.json()
                    progress_bar.progress(job["progress"])
                    status_text.info(job["message"])
                    
                    if job["status"] == "completed":
                        st.session_state.package = job["package"]
                        st.session_state.processing = False
                        status_text.success("Pipeline Complete! Navigate to the other tabs to view.")
                        break
                    elif job["status"] == "error":
                        st.session_state.processing = False
                        status_text.error(f"Pipeline Failed: {job['message']}")
                        break
                time.sleep(2)
            except Exception as e:
                st.error(f"Connection lost: {e}")
                st.session_state.processing = False
                break

# Helper to check if package exists
def check_package():
    if not st.session_state.package:
        st.warning("Please generate an onboarding pipeline in the 'Setup & Upload' tab first.")
        return False
    return True

# --- TAB 2: 30-60-90 TIMELINE ---
with tabs[1]:
    if check_package():
        package = st.session_state.package
        roadmap = package["roadmap"]
        
        st.header(f"Master Roadmap: {roadmap['role_profile']['role_title']}")
        
        weeks = roadmap["weeks"]
        df = pd.DataFrame([{
            "Phase": f"Phase {w['phase_number']}",
            "Week": w["week_number"],
            "Theme": w["theme"],
            "Milestone": w["hands_on_milestone"],
            "Checkpoint": w["manager_checkpoint"] or "—"
        } for w in weeks])
        
        st.dataframe(df, width='stretch', hide_index=True)

# --- TAB 3: DAILY TASKS ---
with tabs[2]:
    if check_package():
        package = st.session_state.package
        tasks = package["daily_tasks"]
        
        st.header("Daily Micro-Action Tasks (CPG 2.0)")
        st.markdown("*Mathematically paced to 20-30 minutes per day.*")
        
        # Simple task browser
        if tasks:
            selected_day = st.selectbox("Select Day", [f"Day {t['day_number']}: {t['topic']}" for t in tasks])
            day_idx = int(selected_day.split(":")[0].replace("Day ", "")) - 1
            
            task = tasks[day_idx]
            st.subheader(f"☀️ Day {task['day_number']}: {task['topic']}")
            
            st.info(f"⏱️ **Time:** {task['estimated_minutes']} mins | 🏢 **Tools:** {', '.join(task['tools_needed']) if task['tools_needed'] else 'None'}")
            
            st.markdown("#### 🎯 Mission")
            st.write(task["daily_mission"])
            
            st.markdown("#### 📜 Core Rules")
            for r in task["sop_principles"]:
                st.markdown(f"- {r}")
                
            if task.get("common_mistakes_to_avoid"):
                st.warning("**Common Mistakes to Avoid:**\n" + "\n".join([f"- {m}" for m in task["common_mistakes_to_avoid"]]))
                
            st.markdown("#### 🛠️ Hands-On Task")
            st.write(task["hands_on_action_task"])
            
            st.checkbox(f"Completed: {task['verification_deliverable']}")

# --- TAB 4: MANAGER GATES ---
with tabs[3]:
    if check_package():
        package = st.session_state.package
        gates = package["manager_gates"]
        
        st.header("Manager 1-on-1 Evaluation Gates")
        st.markdown("*Aligned with Saudi Labor Law (Article 53) Probation Framework.*")
        
        if gates:
            tabs_gates = st.tabs([f"Day {g['gate_day']}" for g in gates])
            
            for i, gate in enumerate(gates):
                with tabs_gates[i]:
                    st.subheader(f"{gate['milestone_name']}")
                    
                    st.markdown("**✅ Competencies to Verify:**")
                    for c in gate["key_competencies_to_verify"]:
                        st.markdown(f"- [ ] {c}")
                        
                    st.markdown("**💬 Interview Questions:**")
                    for q in gate["one_on_one_questions"]:
                        st.markdown(f"- {q}")
                        
                    if gate.get("red_flags"):
                        st.error("**🚩 Red Flags:**\n" + "\n".join([f"- {f}" for f in gate["red_flags"]]))

# --- TAB 5: EXPORT CENTER ---
with tabs[4]:
    if check_package():
        st.header("Export & Integration Center")
        st.write("Download the complete generated onboarding package for Notion, Github, or internal Wikis.")
        
        if st.button("⬇️ Download ZIP Bundle", type="primary"):
            st.markdown(f"**[Click here to download your ZIP bundle directly from the API]({API_URL}/jobs/{st.session_state.job_id}/export)**")

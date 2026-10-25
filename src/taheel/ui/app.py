import streamlit as st
import requests
import time
import pandas as pd

API_URL = "http://localhost:8000/api/v1"

STEP_ORDER = ["ingest", "ontology", "roadmap", "tasks", "gates"]
STEP_LABELS = {
    "ingest": "1. Ingest Document",
    "ontology": "2. Generate Ontology",
    "roadmap": "3. Generate Roadmap",
    "tasks": "4. Generate Daily Tasks",
    "gates": "5. Generate Manager Gates",
}

st.set_page_config(
    page_title="Taheel AI | تأهيل",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "job" not in st.session_state:
    st.session_state.job = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "auto_run" not in st.session_state:
    st.session_state.auto_run = True

st.title("🚀 Taheel AI (نظام التأهيل الذكي)")
st.markdown("**Enterprise 30-60-90 Day Employee Onboarding and Probation Governance Engine**")

tabs = st.tabs([
    "1. Setup and Upload",
    "2. 30-60-90 Timeline",
    "3. Daily Tasks",
    "4. Manager Gates",
    "5. Export Center"
])


def fetch_job():
    """Fetches the latest job state from the API."""
    try:
        res = requests.get(f"{API_URL}/jobs/{st.session_state.job_id}", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def trigger_step(step):
    """Asks the API to run a single pipeline step."""
    try:
        res = requests.post(
            f"{API_URL}/jobs/{st.session_state.job_id}/steps/{step}", timeout=10
        )
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to start step '{step}': {res.text}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Is FastAPI running on port 8000?")
    return None


def _refresh_step_icons(job, placeholders):
    """Updates the icon next to each step in the pipeline checklist."""
    steps_done = job.get("steps_done", [])
    ontology_detail = None
    if job.get("ontology"):
        ontology_detail = f"{job['ontology']['raw_sops_count']} SOPs extracted"
    roadmap_detail = None
    if job.get("roadmap"):
        roadmap_detail = f"{len(job['roadmap']['weeks'])} weeks planned"
    tasks_detail = None
    if job.get("daily_tasks"):
        tasks_detail = f"{len(job['daily_tasks'])} task cards"
    gates_detail = None
    if job.get("manager_gates"):
        gates_detail = f"{len(job['manager_gates'])} evaluation gates"

    step_details = {
        "ingest": "Document text extracted" if "ingest" in steps_done else None,
        "ontology": ontology_detail,
        "roadmap": roadmap_detail,
        "tasks": tasks_detail,
        "gates": gates_detail,
    }
    for step, ph in placeholders.items():
        if step in steps_done:
            icon = "✅"
        elif job["status"] == "error" and job.get("current_step") == step:
            icon = "❌"
        elif job["status"] == "processing" and job.get("current_step") == step:
            icon = "⏳"
        elif job.get("next_step") == step and job["status"] != "error":
            icon = "▶️"
        else:
            icon = "⬜"
        detail = step_details.get(step)
        suffix = f" — {detail}" if detail else ""
        ph.markdown(f"{icon} **{STEP_LABELS[step]}**{suffix}")


def run_pipeline(progress_bar, status_text, step_icon_placeholders):
    """
    Drives the full pipeline (or a single step if auto_run is False).
    Polls every 2 s while a step is processing, then either stops (manual mode)
    or immediately triggers the next step (auto-run mode).
    """
    step_start = time.time()

    while True:
        job = fetch_job()
        if not job:
            st.error("Lost connection to the API.")
            st.session_state.processing = False
            return

        st.session_state.job = job
        elapsed = time.time() - step_start

        progress_bar.progress(min(int(job["progress"]), 100))
        current_label = STEP_LABELS.get(job.get("current_step", ""), "")
        if job["status"] == "processing":
            status_text.info(
                f"⏳ **{current_label}** — {job['message']}  \n"
                f"*Elapsed: {elapsed:.0f}s (model is thinking...)*"
            )
        else:
            status_text.info(job["message"])

        _refresh_step_icons(job, step_icon_placeholders)

        if job["status"] == "completed":
            progress_bar.progress(100)
            status_text.success("🎉 Pipeline complete! Check the other tabs or the Export Center.")
            st.session_state.processing = False
            return

        if job["status"] == "error":
            status_text.error(f"❌ {job['message']}")
            st.session_state.processing = False
            return

        if job["status"] == "ready":
            next_step = job.get("next_step")
            if not next_step:
                st.session_state.processing = False
                return

            if st.session_state.auto_run:
                status_text.info(
                    f"✅ Step done in {elapsed:.0f}s. Auto-starting: **{STEP_LABELS[next_step]}**..."
                )
                triggered = trigger_step(next_step)
                if triggered:
                    st.session_state.job = triggered
                    step_start = time.time()
                else:
                    st.session_state.processing = False
                    return
            else:
                status_text.success(f"✅ {job['message']}")
                st.session_state.processing = False
                return

        time.sleep(2)


# ---------------------------------------------------------------------------
# TAB 1: SETUP AND UPLOAD
# ---------------------------------------------------------------------------
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

    st.session_state.auto_run = st.toggle(
        "⚡ Auto-run all steps (recommended)",
        value=st.session_state.auto_run,
        help="When ON: each step triggers the next automatically. When OFF: click Run Next Step manually.",
    )

    if st.button("Create Job and Ingest Document", type="primary"):
        if uploaded_file is None:
            st.warning("Please upload a document first.")
        else:
            files = {"document": (uploaded_file.name, uploaded_file, "application/octet-stream")}
            data = {
                "company_name": company_name,
                "department": department,
                "role_title": role_title,
                "mentor_name": mentor_name,
                "language": lang_code,
            }
            try:
                res = requests.post(f"{API_URL}/jobs", files=files, data=data, timeout=30)
                if res.status_code == 200:
                    job_data = res.json()
                    st.session_state.job_id = job_data["job_id"]
                    st.session_state.job = job_data
                    st.session_state.processing = True
                    st.success("Job created. Ingesting document...")
                else:
                    st.error(f"Failed to start job: {res.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Is FastAPI running on port 8000?")

    if st.session_state.job_id and st.session_state.job:
        st.markdown("---")
        st.subheader("Pipeline Progress")

        job = st.session_state.job
        step_icon_placeholders = {step: st.empty() for step in STEP_ORDER}
        _refresh_step_icons(job, step_icon_placeholders)

        if st.session_state.processing:
            progress_bar = st.progress(min(int(job["progress"]), 100))
            status_text = st.empty()
            run_pipeline(progress_bar, status_text, step_icon_placeholders)
            job = st.session_state.job
            st.rerun()

        else:
            if job["status"] == "ready":
                st.markdown(f"**Next up:** {STEP_LABELS[job['next_step']]}")
                if not st.session_state.auto_run:
                    if st.button("▶️ Run Next Step", type="primary"):
                        triggered = trigger_step(job["next_step"])
                        if triggered:
                            st.session_state.job = triggered
                            st.session_state.processing = True
                            st.rerun()
                else:
                    if st.button("▶️ Resume Auto-Run", type="primary"):
                        st.session_state.processing = True
                        st.rerun()

            elif job["status"] == "error":
                st.error(f"❌ {job['message']}")
                retry_step = job.get("current_step") or job.get("next_step")
                if retry_step and st.button("🔁 Retry Failed Step", type="primary"):
                    triggered = trigger_step(retry_step)
                    if triggered:
                        st.session_state.job = triggered
                        st.session_state.processing = True
                        st.rerun()

            elif job["status"] == "processing":
                if st.button("🔄 Resume Monitoring"):
                    st.session_state.processing = True
                    st.rerun()

            elif job["status"] == "completed":
                st.success("🎉 All steps complete. Review the other tabs or download the bundle from the Export Center.")


# ---------------------------------------------------------------------------
# TAB 2: 30-60-90 TIMELINE
# ---------------------------------------------------------------------------
with tabs[1]:
    job = st.session_state.job
    if job and job.get("roadmap"):
        roadmap = job["roadmap"]
        st.header(f"Master Roadmap: {roadmap['role_profile']['role_title']}")
        weeks = roadmap["weeks"]
        df = pd.DataFrame([{
            "Phase": f"Phase {w['phase_number']}",
            "Week": w["week_number"],
            "Theme": w["theme"],
            "Milestone": w["hands_on_milestone"],
            "Checkpoint": w["manager_checkpoint"] or "—",
        } for w in weeks])
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("⏳ The roadmap appears here once Step 3 (Generate Roadmap) has run.")


# ---------------------------------------------------------------------------
# TAB 3: DAILY TASKS
# ---------------------------------------------------------------------------
with tabs[2]:
    job = st.session_state.job
    if job and "tasks" in job.get("steps_done", []):
        tasks = job.get("daily_tasks") or []
        st.header("Daily Micro-Action Tasks (CPG 2.0)")
        st.markdown("*Mathematically paced to 20-30 minutes per day.*")
        if tasks:
            selected_day = st.selectbox(
                "Select Day", [f"Day {t['day_number']}: {t['topic']}" for t in tasks]
            )
            day_idx = int(selected_day.split(":")[0].replace("Day ", "")) - 1
            task = tasks[day_idx]
            st.subheader(f"☀️ Day {task['day_number']}: {task['topic']}")
            tools_str = ", ".join(task["tools_needed"]) if task["tools_needed"] else "None"
            st.info(f"⏱️ **Time:** {task['estimated_minutes']} mins | 🏢 **Tools:** {tools_str}")
            st.markdown("#### 🎯 Mission")
            st.write(task["daily_mission"])
            st.markdown("#### 📜 Core Rules")
            for r in task["sop_principles"]:
                st.markdown(f"- {r}")
            if task.get("common_mistakes_to_avoid"):
                mistakes = "\n".join([f"- {m}" for m in task["common_mistakes_to_avoid"]])
                st.warning(f"**Common Mistakes to Avoid:**\n{mistakes}")
            st.markdown("#### 🛠️ Hands-On Task")
            st.write(task["hands_on_action_task"])
            st.checkbox(f"Completed: {task['verification_deliverable']}")
        else:
            st.warning("No daily tasks were generated (the ontology contained no SOPs).")
    else:
        st.info("⏳ Daily tasks appear here once Step 4 (Generate Daily Tasks) has run.")


# ---------------------------------------------------------------------------
# TAB 4: MANAGER GATES
# ---------------------------------------------------------------------------
with tabs[3]:
    job = st.session_state.job
    if job and "gates" in job.get("steps_done", []):
        gates = job.get("manager_gates") or []
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
                        flags = "\n".join([f"- {f}" for f in gate["red_flags"]])
                        st.error(f"**🚩 Red Flags:**\n{flags}")
        else:
            st.warning("No manager gates were generated.")
    else:
        st.info("⏳ Manager gates appear here once Step 5 (Generate Manager Gates) has run.")


# ---------------------------------------------------------------------------
# TAB 5: EXPORT CENTER
# ---------------------------------------------------------------------------
with tabs[4]:
    job = st.session_state.job
    if job and job.get("package"):
        st.header("Export and Integration Center")
        st.write("Download the complete generated onboarding package for Notion, Github, or internal Wikis.")
        if st.button("⬇️ Download ZIP Bundle", type="primary"):
            st.markdown(
                f"**[Click here to download your ZIP bundle directly from the API]"
                f"({API_URL}/jobs/{st.session_state.job_id}/export)**"
            )
    else:
        st.info("⬇️ Export unlocks once all five pipeline steps are complete.")

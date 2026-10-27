# 🚀 Taheel AI (تأهيل)

**AI-Powered 30-60-90 Day Employee Onboarding & Probation Governance Engine**

> Bilingual (Arabic & English) · Aligned with Saudi Labor Law Article 53 · Role-Adaptive

---

## ⚠️ Proof of Concept Disclaimer

**This project is a Proof of Concept (POC)** demonstrating how AI can transform dense corporate handbooks, SOPs, and operational manuals into structured, personalized 30-60-90 day onboarding programs.

The idea behind Taheel AI is that it could be **highly beneficial for Saudi companies** — particularly those navigating the 90-day probation window defined by **Article 53 of the Saudi Labor Law (فترة التجربة)** — by solving three critical pain points:

1. **Probation Blindspot:** Most companies lack a structured daily framework for the 90-day probation period, leading to subjective last-minute decisions.
2. **Cognitive Overload:** New hires are buried in hundreds of pages of documentation on Day 1, causing burnout and slow time-to-productivity.
3. **Manager Time Poverty:** Line managers don't have the bandwidth to write tailored day-by-day training plans for each new hire.

### AI Dependency & Output Quality

As a POC, the quality of the generated onboarding programs is **directly dependent on the AI model used**. Key considerations:

- **Stronger models** (e.g., Gemini 2.5 Pro, Claude 3.5 Sonnet, Mistral Large) will produce more accurate, nuanced, and contextually appropriate outputs.
- **Weaker or smaller models** may produce generic content, miss role-specific nuances, or struggle with bilingual Arabic/English generation.
- The system uses **structured JSON output** prompts — models with strong instruction-following and JSON capabilities will perform best.
- **Arabic language quality** varies significantly across models. For Arabic-heavy outputs, test thoroughly with your chosen provider.

> This is **not** production-ready software. It is a demonstration of the concept and architecture. Further refinement, testing, prompt engineering, and model evaluation would be needed before any production deployment.

---

## 📋 What It Does

Taheel AI ingests company documentation (PDFs, text files, Markdown SOPs) and generates:

| Output | Description |
|:---|:---|
| **Role-Adaptive Ontology** | Extracts and filters SOPs relevant to a specific role, grouped into three 30-day phases |
| **30-60-90 Day Roadmap** | A structured Markdown roadmap with weekly milestones, tasks, and manager checkpoints |
| **Daily Micro-Action Cards** | 20–30 minute daily learning tasks with missions, SOP rules, hands-on exercises, and checklists |
| **Manager Evaluation Gates** | Formal 1-on-1 review rubrics at Days 14, 30, 60, and 90 with probation readiness scoring |
| **Export Packages** | Notion-ready templates and downloadable `.zip` archives |

---

## 🏗️ Architecture

```
Taheel_AI/
├── src/taheel/
│   ├── schema.py              # Pydantic domain models
│   ├── llm_provider.py        # Multi-provider LLM client with fallback chain
│   ├── ingestion/             # PDF extraction & Arabic text normalization
│   ├── generators/            # Ontology, Roadmap, Daily Tasks, Manager Gates
│   ├── pacing/                # Cognitive load balancer (20–30 min/day caps)
│   ├── exporters/             # Notion/Markdown zip packager
│   ├── api/                   # FastAPI backend
│   └── ui/                    # Streamlit web dashboard
├── data/
│   ├── sample_sops/           # Sample SOP files for testing
│   └── outputs/               # Generated onboarding packages
├── tests/                     # Pytest test suite
├── requirements.txt
├── TAHEEL_SPEC.md             # Full product specification
└── IMPLEMENTATION_PLAN.md     # Technical implementation plan
```

---

## 🛠️ Setup & Installation

### Prerequisites

- **Python 3.10+**
- **Conda** (the project uses a conda environment called `dawn`)
- At least one LLM API key (see [LLM Configuration](#-llm-configuration) below)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Taheel_AI.git
cd Taheel_AI
```

### 2. Create & Activate the Conda Environment

```bash
conda create -n dawn python=3.11 -y
conda activate dawn
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Then open `.env` in your editor and set the required values (see section below).

---

## 🔑 LLM Configuration

Taheel AI supports **three LLM providers** with automatic fallback. You only need **at least one** configured, but you can set up all three for resilience.

### `.env` File Structure

```env
# ──────────────────────────────────────────────
# Primary Provider: Google Gemini
# ──────────────────────────────────────────────
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.8-flash

# ──────────────────────────────────────────────
# Fallback 1: OpenRouter
# ──────────────────────────────────────────────
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# ──────────────────────────────────────────────
# Fallback 2: Mistral AI
# ──────────────────────────────────────────────
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest

# ──────────────────────────────────────────────
# Provider Selection & Fallback Order
# ──────────────────────────────────────────────
PRIMARY_LLM_PROVIDER=gemini
LLM_FALLBACK_CHAIN=openrouter,mistral

# ──────────────────────────────────────────────
# Server Settings
# ──────────────────────────────────────────────
TAHEEL_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

### Getting API Keys

| Provider | Where to Get a Key | Notes |
|:---|:---|:---|
| **Google Gemini** | [Google AI Studio](https://aistudio.google.com/apikey) | Free tier available. Uses the OpenAI-compatible endpoint. |
| **OpenRouter** | [openrouter.ai/keys](https://openrouter.ai/keys) | Aggregator — access to Claude, GPT, Llama, and more via one key. |
| **Mistral AI** | [console.mistral.ai](https://console.mistral.ai/api-keys/) | Direct Mistral API access. |

### How Fallback Works

The system tries providers in order: **Primary → Fallback 1 → Fallback 2**. If the primary provider fails (network error, rate limit, invalid key), it automatically retries with the next provider in the chain. You only need to configure the providers you intend to use — leave the others as placeholder values or remove them.

---

## 🚀 Running the Application

Taheel AI has two components that run simultaneously: the **FastAPI backend** and the **Streamlit UI**.

### Start the API Server

```bash
conda activate dawn
uvicorn src.taheel.api.main:app --reload
```

The API will be available at `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

### Start the Streamlit Dashboard

In a separate terminal:

```bash
conda activate dawn
streamlit run src/taheel/ui/app.py
```

The web dashboard will open at `http://localhost:8501`.

### Quick Test with Sample Data

A sample SOP file is included at `data/sample_sops/fintech_customer_ops_sop.md`. You can upload it through the Streamlit UI or use the API directly to test the full pipeline.

---

## 🧪 Running Tests

```bash
conda activate dawn
pytest
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

© 2026 Youssef ElNahas

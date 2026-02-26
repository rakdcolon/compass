# Compass — AI Benefits Navigator
### Amazon Nova Hackathon Submission | Category: Agentic AI

> **"Every year, $30 billion in government benefits go unclaimed. Compass changes that."**

Compass is an AI-powered social services navigator that helps vulnerable populations — elderly adults, people with disabilities, immigrants, and low-income families — discover and apply for government benefits they are entitled to but may not know about.

---

## The Problem

The U.S. has hundreds of federal, state, and local benefit programs, but accessing them is a nightmare:
- **$30 billion** in benefits go unclaimed annually (NCOA research)
- **7 million** eligible people don't receive SNAP food assistance
- **60%** of eligible seniors never enroll in Medicare Savings Programs
- Barriers include: complexity, language gaps, lack of digital literacy, and stigma

Compass tears down these barriers through conversational AI.

---

## Amazon Nova Integration

Compass uses **all four** Amazon Nova capabilities:

| Model | Usage |
|-------|-------|
| **Nova 2 Lite** | Multi-agent orchestrator with tool use — determines benefit eligibility, finds resources, analyzes documents, generates action plans |
| **Nova 2 Sonic** | Real-time voice conversation — natural, multilingual speech interface accessible to those who can't type |
| **Nova Multimodal Embeddings** | Semantic document-to-program matching — embeds uploaded pay stubs and documents to find the most relevant benefit programs |
| **Nova Act** | Browser automation — automatically navigates government portals (benefits.gov, healthcare.gov, ssa.gov) and pre-fills applications |

---

## Architecture

```
Browser (Voice/Text/Document)
         │
    WebSocket / REST
         │
    FastAPI Backend
    ├── Nova 2 Sonic     ← Voice bidirectional streaming (HTTP/2)
    ├── Nova 2 Lite      ← Multi-agent orchestrator with tool use
    │   ├── check_benefit_eligibility()
    │   ├── find_local_resources()
    │   ├── analyze_document()      ← Nova Lite vision
    │   └── create_action_plan()
    ├── Nova Embeddings  ← Document → program semantic matching
    └── Nova Act         ← Portal automation (browser agents)
```

---

## Features

### Voice Interface (Nova 2 Sonic)
- Speak naturally about your situation in English, Spanish, or French
- Real-time bidirectional audio streaming (PCM 16kHz)
- Accessible to elderly, disabled, and non-literate users

### Intelligent Eligibility Check (Nova 2 Lite)
Checks eligibility for 10+ federal programs including:
- SNAP (food assistance)
- Medicaid & CHIP (healthcare)
- TANF (cash assistance)
- WIC (nutrition for mothers and children)
- LIHEAP (energy bill assistance)
- SSI (disability income)
- Section 8 (housing vouchers)
- EITC (earned income tax credit)
- Medicare Savings Programs

### Document Analysis (Nova Vision + Embeddings)
- Upload pay stubs, medical records, utility bills, or ID documents
- Nova 2 Lite extracts income, dates, employer, and key fields
- Nova Multimodal Embeddings matches document semantics to relevant programs
- Automatically populates eligibility check with extracted data

### Portal Automation (Nova Act)
- Nova Act agents navigate government websites automatically
- Pre-fills application forms with user's information
- Guides users through the application process step by step

### Local Resource Discovery
- Food banks, free health clinics, emergency shelters
- Legal aid, employment services, mental health support
- Always returns the 2-1-1 national helpline

---

## Setup

### Prerequisites
- Python 3.11+
- AWS account with Bedrock access (us-east-1 recommended)
- Nova Act API key (from nova.amazon.com/act)

### Installation

```bash
# Clone and enter directory
cd compass

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and Nova Act API key
```

### Configuration

```env
# .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
NOVA_ACT_API_KEY=your_nova_act_key
```

### Run

```bash
python run.py
# Open http://localhost:8000
```

### Demo Instructions

```bash
python run.py --demo
```

---

## Demo Flow

1. **Open** http://localhost:8000
2. **Click the microphone** and say:
   > *"I lost my job last month. I'm a single mom with two kids in California. We make about $2,000 a month and I'm struggling to pay for food and my kids' doctor visits."*
3. **Compass** (Nova 2 Sonic) responds and asks follow-up questions
4. **Upload a pay stub** — Nova vision extracts income automatically
5. **See results** — SNAP, Medicaid for kids, TANF, WIC, LIHEAP all appear
6. **Click "Nova Act → Auto-fill"** — watch the agent navigate to benefits.gov
7. **Get your action plan** — prioritized steps to access each program

---

## Project Structure

```
compass/
├── README.md
├── requirements.txt
├── .env.example
├── run.py                        # Entry point
├── backend/
│   ├── main.py                   # FastAPI app
│   ├── config.py                 # Configuration
│   ├── agents/
│   │   └── orchestrator.py       # Nova 2 Lite multi-agent loop
│   ├── services/
│   │   ├── nova_sonic.py         # Nova 2 Sonic voice service
│   │   ├── nova_lite.py          # Nova 2 Lite wrapper
│   │   └── nova_embeddings.py    # Nova Embeddings service
│   ├── tools/
│   │   ├── eligibility.py        # Benefits eligibility tool
│   │   ├── resources.py          # Local resource finder tool
│   │   └── document_tool.py      # Document analysis tool
│   └── data/
│       └── benefits_db.py        # Benefits programs knowledge base
└── frontend/
    ├── index.html                # Single-page app
    ├── css/styles.css
    └── js/
        ├── app.js                # App controller
        ├── voice.js              # Audio capture/playback
        └── api.js                # API client
```

---

## Social Impact

Compass directly addresses the **$30B benefits access gap** by:

1. **Removing complexity** — conversational interface instead of 50-page applications
2. **Breaking language barriers** — multilingual voice interface
3. **Serving non-digital users** — voice-first design for elderly and disabled
4. **Automating the hard part** — Nova Act fills out forms automatically
5. **Eliminating shame** — empathetic AI framing removes stigma

**Target populations**: Elderly adults, people with disabilities, recent immigrants, single parents, newly unemployed workers, people experiencing homelessness.

---

## Technical Highlights

- **True multi-agent system** with Nova 2 Lite tool use and agentic loop
- **Bidirectional voice streaming** via HTTP/2 with Nova 2 Sonic
- **Multimodal document understanding** — both vision extraction and semantic embedding
- **Browser automation** with Nova Act for end-to-end application assistance
- **Production-ready FastAPI** backend with WebSocket support
- **Responsive frontend** with real-time waveform visualization

---

## License

MIT — Built for the Amazon Nova Hackathon.

**#AmazonNova**

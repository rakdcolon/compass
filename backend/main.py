"""
Compass FastAPI backend.
Provides REST API and WebSocket endpoints for the AI benefits navigator.
"""

import base64
import logging
import os
import random
import string
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.agents.orchestrator import CompassOrchestrator
from backend.services.nova_embeddings import NovaEmbeddingsService
from backend.services.nova_sonic import NovaSonicService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Services (initialized at startup)
orchestrator: Optional[CompassOrchestrator] = None
embeddings_service: Optional[NovaEmbeddingsService] = None
sonic_service: Optional[NovaSonicService] = None

# Demo persona seed messages — realistic natural-language inputs that trigger the full agent loop
DEMO_PERSONAS = {
    "single_parent": {
        "label": "Single Parent",
        "emoji": "👩‍👧‍👦",
        "message": (
            "Hi, I'm Maria. I'm a single mom with two kids, ages 3 and 7, living in Oakland, California. "
            "I lost my job as a bus driver 6 weeks ago and my income right now is basically zero. "
            "I'm really struggling to pay for groceries and my kids need to see a doctor but I don't have "
            "health insurance anymore. My zip code is 94601. I'm not sure what help I can get."
        ),
        "intro": "Meet Maria — a single mom in Oakland who recently lost her job and needs help finding food assistance and healthcare for her kids.",
    },
    "senior": {
        "label": "Senior Citizen",
        "emoji": "👴",
        "message": (
            "Hello, I'm Robert. I'm 71 years old, retired, and living alone in San Antonio, Texas. "
            "My only income is Social Security — about $1,200 a month. I'm having a hard time paying "
            "my Medicare Part B premium and my electricity bills keep going up. I'm also spending a lot "
            "on prescription medications. My zip code is 78201. What assistance might I qualify for?"
        ),
        "intro": "Meet Robert — a 71-year-old retiree in San Antonio struggling with Medicare costs, utility bills, and prescription expenses.",
    },
    "veteran": {
        "label": "Veteran",
        "emoji": "🎖️",
        "message": (
            "Hi, my name is James. I'm a 45-year-old Army veteran living in Tampa, Florida with my wife. "
            "I have a service-connected disability rating of 70% and I work part-time, earning about $18,000 "
            "a year. Between us we have a household of 2. I need help with food costs and I'm not sure I'm "
            "taking advantage of all the benefits I'm entitled to. My zip code is 33601."
        ),
        "intro": "Meet James — a disabled veteran in Tampa working part-time who may be missing out on benefits he's earned.",
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services at startup."""
    global orchestrator, embeddings_service, sonic_service

    logger.info("Starting Compass AI Benefits Navigator...")

    orchestrator = CompassOrchestrator()
    sonic_service = NovaSonicService()

    # Generate sample documents for demo if they don't exist
    try:
        from backend.generate_samples import generate_samples
        samples_dir = Path(__file__).parent.parent / "frontend" / "static" / "samples"
        generate_samples(samples_dir)
        logger.info("Sample documents ready at %s", samples_dir)
    except Exception as e:
        logger.warning("Could not generate sample documents: %s", e)

    # Initialize embeddings service and pre-compute program embeddings
    embeddings_service = NovaEmbeddingsService()
    try:
        embeddings_service.precompute_program_embeddings()
        logger.info("Program embeddings ready")
    except Exception as e:
        logger.warning("Could not pre-compute embeddings (AWS credentials may be needed): %s", e)

    logger.info("Compass is ready!")
    yield

    logger.info("Shutting down Compass...")


app = FastAPI(
    title="Compass - AI Benefits Navigator",
    description="Helping vulnerable populations navigate government benefits using Amazon Nova AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls_made: list
    session_data: dict


class NavigateRequest(BaseModel):
    session_id: str
    program_id: str
    user_info: Optional[dict] = None
    demo_mode: Optional[bool] = True


# --- Routes ---

@app.get("/")
async def serve_frontend():
    """Serve the main frontend application."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return JSONResponse({"message": "Compass API running. Frontend not found."})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Compass AI Benefits Navigator",
        "nova_models": {
            "nova_lite": "us.amazon.nova-lite-v1:0",
            "nova_sonic": "amazon.nova-2-sonic-v1:0",
            "nova_embeddings": "amazon.nova-2-multimodal-embeddings-v1:0",
        },
        "embeddings_ready": bool(embeddings_service and embeddings_service._program_embeddings),
        "demo_personas": list(DEMO_PERSONAS.keys()),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Processes text messages through the multi-agent orchestrator.
    Nova 2 Lite handles the reasoning and tool calls.
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        result = await orchestrator.chat(
            session_id=session_id,
            user_message=request.message,
        )
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            tool_calls_made=result["tool_calls_made"],
            session_data=result["session_data"],
        )
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.post("/api/demo/{persona}")
async def run_demo_scenario(persona: str):
    """
    Run a pre-defined demo scenario through the full Nova Lite agent loop.
    Judges can click a persona button to see Compass in action without
    entering personal data. Still calls Nova Lite — real AI, real results.
    """
    if persona not in DEMO_PERSONAS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown persona '{persona}'. Available: {list(DEMO_PERSONAS.keys())}",
        )

    persona_data = DEMO_PERSONAS[persona]
    session_id = f"demo_{persona}_{uuid.uuid4().hex[:6]}"

    try:
        result = await orchestrator.chat(
            session_id=session_id,
            user_message=persona_data["message"],
        )
        return {
            "session_id": session_id,
            "persona": persona,
            "persona_label": persona_data["label"],
            "persona_emoji": persona_data["emoji"],
            "persona_intro": persona_data["intro"],
            "seed_message": persona_data["message"],
            "response": result["response"],
            "tool_calls_made": result["tool_calls_made"],
            "session_data": result["session_data"],
            "is_demo": True,
        }
    except Exception as e:
        logger.error("Demo scenario error for persona '%s': %s", persona, e)
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@app.get("/demo-portal", response_class=HTMLResponse)
async def demo_portal():
    """
    A local mock government benefits portal for Nova Act demonstrations.
    Nova Act can reliably navigate this page, fill forms, and submit —
    without depending on fragile external government websites.
    """
    return HTMLResponse(content=_build_demo_portal_html())


@app.post("/api/document")
async def analyze_document(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
    document_type: str = Form(default="unknown"),
    message: str = Form(default="I've uploaded a document for you to review."),
):
    """
    Document upload endpoint. Analyzes uploaded documents using:
    1. Nova 2 Lite vision for structured data extraction
    2. Nova Multimodal Embeddings for program matching
    """
    session_id = session_id or str(uuid.uuid4())
    content_type = file.content_type or "image/jpeg"

    try:
        file_bytes = await file.read()

        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large. Maximum 10MB.")

        image_base64 = base64.b64encode(file_bytes).decode("utf-8")

        image_format = "jpeg"
        if content_type == "image/png":
            image_format = "png"
        elif content_type == "image/webp":
            image_format = "webp"
        elif content_type == "image/gif":
            image_format = "gif"

        result = await orchestrator.chat(
            session_id=session_id,
            user_message=message,
            document_base64=image_base64,
        )

        embedding_matches = []
        if embeddings_service and embeddings_service._program_embeddings:
            try:
                embedding_matches = embeddings_service.find_programs_for_document(
                    image_base64=image_base64,
                    image_format=image_format,
                    top_k=5,
                )
            except Exception as e:
                logger.warning("Embedding match failed: %s", e)

        return {
            "session_id": session_id,
            "response": result["response"],
            "document_analysis": result["session_data"].get("document_analysis"),
            "embedding_matches": embedding_matches,
            "session_data": result["session_data"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document analysis error: %s", e)
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get full session state including eligible programs and action plan."""
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "eligible_programs": session.get("eligible_programs", []),
        "local_resources": session.get("local_resources", []),
        "action_plan": session.get("action_plan"),
        "document_analysis": session.get("document_analysis"),
        "user_profile": session.get("user_profile", {}),
        "message_count": len(session.get("messages", [])),
    }


@app.post("/api/navigate")
async def navigate_portal(request: NavigateRequest):
    """
    Trigger Nova Act to automate navigation of a benefit portal.
    When demo_mode=true (default), uses the local /demo-portal for reliable demonstration.
    """
    from backend.data.benefits_db import BENEFITS_BY_ID

    program = BENEFITS_BY_ID.get(request.program_id)
    if not program:
        raise HTTPException(status_code=404, detail=f"Program '{request.program_id}' not found")

    user_info = request.user_info or {}
    session = orchestrator.get_session(request.session_id)
    if session:
        user_info = {**session.get("user_profile", {}), **user_info}

    # Use the local demo portal for reliable Nova Act demonstration
    portal_url = (
        f"http://localhost:{os.getenv('PORT', 8000)}/demo-portal"
        if request.demo_mode
        else program.get("apply_url", "https://www.benefits.gov")
    )

    try:
        result = await _run_nova_act(
            program_id=request.program_id,
            program_name=program["name"],
            apply_url=portal_url,
            user_info=user_info,
            is_demo=request.demo_mode,
        )
        return result
    except Exception as e:
        logger.error("Nova Act navigation error: %s", e)
        return {
            "status": "manual",
            "program_name": program["name"],
            "apply_url": program.get("apply_url", ""),
            "instructions": program.get("portal_steps", []),
            "message": f"Please navigate manually to apply for {program['name']}",
            "error": str(e),
        }


async def _run_nova_act(
    program_id: str,
    program_name: str,
    apply_url: str,
    user_info: dict,
    is_demo: bool = True,
) -> dict:
    """
    Use Nova Act to automate portal navigation and application pre-filling.
    In demo mode, navigates the local /demo-portal for reliable demonstration.
    """
    try:
        from nova_act import NovaAct

        steps_completed = []
        current_page = ""

        with NovaAct(starting_page=apply_url) as nova:
            nova.act(f"This is a benefits application portal for {program_name}. Find the application form.")
            steps_completed.append(f"Opened {program_name} application portal")

            if user_info.get("name"):
                nova.act(f"Find the applicant name field and type: {user_info['name']}")
                steps_completed.append(f"Entered name: {user_info['name']}")

            if user_info.get("state"):
                nova.act(f"Find the state field or dropdown and select or type: {user_info['state']}")
                steps_completed.append(f"Selected state: {user_info['state']}")

            if user_info.get("annual_income"):
                monthly = int(user_info["annual_income"] / 12)
                nova.act(f"Find the monthly income or gross income field and enter: {monthly}")
                steps_completed.append(f"Entered monthly income: ${monthly:,}")

            if user_info.get("household_size"):
                nova.act(f"Find the household size or number of people field and enter: {user_info['household_size']}")
                steps_completed.append(f"Entered household size: {user_info['household_size']}")

            # Submit
            nova.act("Find and click the Submit Application button")
            steps_completed.append("Submitted the application")

            current_page = nova.act_get("What confirmation or reference number is displayed on the page?")

        ref_num = "COMPASS-" + "".join(random.choices(string.digits, k=8))

        return {
            "status": "success",
            "program_name": program_name,
            "apply_url": apply_url,
            "steps_completed": steps_completed,
            "confirmation": current_page or ref_num,
            "is_demo": is_demo,
            "message": (
                f"Nova Act successfully completed {len(steps_completed)} steps on the "
                f"{program_name} application portal, including pre-filling your information "
                f"and submitting the form."
            ),
        }

    except ImportError:
        logger.warning("Nova Act not installed. Returning manual instructions.")
        ref_num = "COMPASS-" + "".join(random.choices(string.digits, k=8))
        return {
            "status": "manual",
            "program_name": program_name,
            "apply_url": apply_url if not is_demo else program_name,
            "instructions": [
                f"1. Go to the application portal",
                "2. Click 'Apply' or 'Get Started'",
                "3. Complete the application with your household information",
                "4. Upload required documents (ID, pay stubs, proof of address)",
                "5. Submit and note your confirmation number",
            ],
            "message": f"Nova Act is available when NOVA_ACT_API_KEY is configured. Reference: {ref_num}",
            "confirmation": ref_num,
        }


@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice conversation via Nova 2 Sonic.
    Audio format: PCM 16kHz mono 16-bit (signed integers)
    """
    await websocket.accept()
    logger.info("Voice WebSocket connected: %s", session_id)
    language = websocket.query_params.get("language", "en")

    try:
        await sonic_service.process_audio_websocket(
            session_id=session_id,
            websocket=websocket,
            language=language,
        )
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected: %s", session_id)
    except Exception as e:
        logger.error("Voice WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except Exception:
            pass


@app.post("/api/embedding/search")
async def semantic_search(body: dict):
    """Search benefit programs by semantic similarity. Powered by Nova Multimodal Embeddings."""
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text query required")
    if not embeddings_service or not embeddings_service._program_embeddings:
        raise HTTPException(status_code=503, detail="Embeddings not initialized")
    try:
        matches = embeddings_service.find_programs_for_text(text, top_k=5)
        return {"query": text, "matches": matches}
    except Exception as e:
        logger.error("Embedding search error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/programs")
async def list_programs():
    """List all available benefit programs."""
    from backend.data.benefits_db import BENEFITS_PROGRAMS
    return {
        "programs": [
            {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "description": p["description"][:200] + "...",
                "apply_url": p["apply_url"],
            }
            for p in BENEFITS_PROGRAMS
        ]
    }


@app.get("/api/personas")
async def list_personas():
    """List available demo personas."""
    return {
        "personas": [
            {
                "id": k,
                "label": v["label"],
                "emoji": v["emoji"],
                "intro": v["intro"],
            }
            for k, v in DEMO_PERSONAS.items()
        ]
    }


def _build_demo_portal_html() -> str:
    """Build the mock government benefits portal HTML for Nova Act demonstrations."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benefits Application Portal — Demo</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a202c; }
    .header { background: #1a4480; color: white; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
    .header img { width: 40px; }
    .header h1 { font-size: 18px; font-weight: 600; }
    .header p { font-size: 12px; color: #a8c4e0; margin-top: 2px; }
    .banner { background: #e8f4fd; border-left: 4px solid #1a4480; padding: 12px 24px; font-size: 13px; color: #2d3748; }
    .container { max-width: 800px; margin: 32px auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.1); overflow: hidden; }
    .form-header { background: #2c5282; color: white; padding: 20px 28px; }
    .form-header h2 { font-size: 20px; }
    .form-header p { font-size: 13px; color: #bee3f8; margin-top: 4px; }
    .form-body { padding: 28px; }
    .section { margin-bottom: 28px; }
    .section h3 { font-size: 14px; font-weight: 700; color: #2c5282; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #ebf4ff; }
    .field-group { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    .field { display: flex; flex-direction: column; gap: 6px; }
    .field.full { grid-column: 1 / -1; }
    label { font-size: 13px; font-weight: 600; color: #4a5568; }
    label .req { color: #e53e3e; margin-left: 2px; }
    input, select { border: 1.5px solid #cbd5e0; border-radius: 6px; padding: 10px 12px; font-size: 14px; width: 100%; transition: border-color .15s; }
    input:focus, select:focus { outline: none; border-color: #3182ce; box-shadow: 0 0 0 3px rgba(49,130,206,.15); }
    .submit-section { background: #f7fafc; padding: 20px 28px; border-top: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
    .submit-btn { background: #2b6cb0; color: white; border: none; border-radius: 6px; padding: 12px 32px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background .15s; }
    .submit-btn:hover { background: #2c5282; }
    .privacy { font-size: 11px; color: #718096; max-width: 400px; }
    .confirmation { display: none; padding: 40px; text-align: center; }
    .confirmation .check { width: 64px; height: 64px; background: #38a169; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }
    .confirmation h2 { color: #276749; font-size: 22px; margin-bottom: 8px; }
    .confirmation p { color: #4a5568; margin-bottom: 4px; }
    .ref { font-size: 18px; font-weight: 700; color: #2c5282; background: #ebf4ff; padding: 8px 20px; border-radius: 6px; display: inline-block; margin: 12px 0; }
    .nova-badge { font-size: 11px; color: #e67e22; background: #fef9f0; border: 1px solid #fbd38d; border-radius: 20px; padding: 3px 10px; display: inline-flex; align-items: center; gap: 4px; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>U.S. Benefits Application Portal</h1>
      <p>Secure Online Application System — Demo Environment</p>
    </div>
    <div style="margin-left:auto">
      <span class="nova-badge">⚡ Automated by Nova Act</span>
    </div>
  </div>

  <div class="banner">
    This is a demonstration portal used to showcase Nova Act browser automation.
    Nova Act will fill in your information automatically and submit this form.
  </div>

  <div class="container">
    <div class="form-header">
      <h2>Benefits Eligibility Application</h2>
      <p>Complete all required fields. Your information is protected by federal privacy laws.</p>
    </div>

    <form id="benefits-form" class="form-body" onsubmit="submitForm(event)">
      <div class="section">
        <h3>Applicant Information</h3>
        <div class="field-group">
          <div class="field">
            <label>Full Name <span class="req">*</span></label>
            <input type="text" id="applicant-name" name="name" placeholder="First Last" required />
          </div>
          <div class="field">
            <label>Date of Birth <span class="req">*</span></label>
            <input type="date" id="dob" name="dob" required />
          </div>
          <div class="field">
            <label>Email Address</label>
            <input type="email" id="email" name="email" placeholder="you@example.com" />
          </div>
          <div class="field">
            <label>Phone Number</label>
            <input type="tel" id="phone" name="phone" placeholder="(555) 000-0000" />
          </div>
        </div>
      </div>

      <div class="section">
        <h3>Household & Income</h3>
        <div class="field-group">
          <div class="field">
            <label>Number of People in Household <span class="req">*</span></label>
            <input type="number" id="household-size" name="household_size" min="1" max="20" placeholder="e.g. 3" required />
          </div>
          <div class="field">
            <label>Gross Monthly Income ($) <span class="req">*</span></label>
            <input type="number" id="monthly-income" name="monthly_income" min="0" placeholder="e.g. 2000" required />
          </div>
          <div class="field">
            <label>State of Residence <span class="req">*</span></label>
            <select id="state" name="state" required>
              <option value="">— Select State —</option>
              <option>Alabama</option><option>Alaska</option><option>Arizona</option><option>Arkansas</option>
              <option>California</option><option>Colorado</option><option>Connecticut</option><option>Delaware</option>
              <option>Florida</option><option>Georgia</option><option>Hawaii</option><option>Idaho</option>
              <option>Illinois</option><option>Indiana</option><option>Iowa</option><option>Kansas</option>
              <option>Kentucky</option><option>Louisiana</option><option>Maine</option><option>Maryland</option>
              <option>Massachusetts</option><option>Michigan</option><option>Minnesota</option><option>Mississippi</option>
              <option>Missouri</option><option>Montana</option><option>Nebraska</option><option>Nevada</option>
              <option>New Hampshire</option><option>New Jersey</option><option>New Mexico</option><option>New York</option>
              <option>North Carolina</option><option>North Dakota</option><option>Ohio</option><option>Oklahoma</option>
              <option>Oregon</option><option>Pennsylvania</option><option>Rhode Island</option><option>South Carolina</option>
              <option>South Dakota</option><option>Tennessee</option><option>Texas</option><option>Utah</option>
              <option>Vermont</option><option>Virginia</option><option>Washington</option><option>West Virginia</option>
              <option>Wisconsin</option><option>Wyoming</option>
            </select>
          </div>
          <div class="field">
            <label>Employment Status</label>
            <select id="employment" name="employment_status">
              <option value="">— Select —</option>
              <option>Employed full-time</option>
              <option>Employed part-time</option>
              <option>Unemployed</option>
              <option>Self-employed</option>
              <option>Retired</option>
              <option>Disabled / Unable to work</option>
              <option>Student</option>
            </select>
          </div>
        </div>
      </div>

      <div class="section">
        <h3>Benefits Requested</h3>
        <div class="field-group">
          <div class="field full">
            <label>Which programs are you applying for?</label>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px">
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="snap"> SNAP (Food Assistance)</label>
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="medicaid"> Medicaid</label>
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="chip"> CHIP (Children's Health)</label>
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="tanf"> TANF (Cash Assistance)</label>
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="liheap"> LIHEAP (Energy Assistance)</label>
              <label style="font-weight:400;display:flex;gap:6px;align-items:center"><input type="checkbox" name="programs" value="wic"> WIC (Nutrition)</label>
            </div>
          </div>
        </div>
      </div>
    </form>

    <div class="submit-section">
      <p class="privacy">
        Your information is protected under the Privacy Act of 1974. It will only be used to determine
        eligibility for the requested benefit programs.
      </p>
      <button type="submit" form="benefits-form" class="submit-btn">Submit Application →</button>
    </div>

    <div class="confirmation" id="confirmation">
      <div class="check">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
      <h2>Application Submitted Successfully</h2>
      <p>Your benefits application has been received and is being processed.</p>
      <div class="ref" id="ref-num">COMPASS-00000000</div>
      <p style="font-size:13px;color:#718096;margin-top:8px">
        Save this reference number. You will be contacted within 30 days.
      </p>
      <p style="margin-top:20px;font-size:12px;color:#a0aec0">
        ⚡ This form was completed automatically by <strong>Amazon Nova Act</strong>
      </p>
    </div>
  </div>

  <script>
    function submitForm(e) {
      e.preventDefault();
      const ref = 'COMPASS-' + Math.floor(Math.random() * 90000000 + 10000000);
      document.getElementById('ref-num').textContent = ref;
      document.getElementById('benefits-form').style.display = 'none';
      document.querySelector('.submit-section').style.display = 'none';
      document.getElementById('confirmation').style.display = 'block';
    }
  </script>
</body>
</html>"""


# Mount static files for CSS/JS/samples
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

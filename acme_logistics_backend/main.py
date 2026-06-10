
import os
import re
import json
import logging
import asyncio
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from dotenv import load_dotenv

from database import init_db, save_trip, update_trip_status, TripDetail, get_all_trips
from agent_config import get_agent_config, get_agent_prompts

# Load environment variables from .env file
load_dotenv()

# Configuration
BOLNA_API_URL = os.getenv("BOLNA_API_URL", "https://api.bolna.ai")
BOLNA_API_KEY = os.getenv("BOLNA_API_KEY", "your_bolna_api_key_here")
AGENT_ID = os.getenv("BOLNA_AGENT_ID", "your_bolna_agent_id")  # Updated with your active agent ID
CALLBACK_RETRY_MINUTES = 15
MAX_RETRIES = 3

# Directory for saving per-call transcript JSON files
TRANSCRIPTS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "call_transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI(title="ACME Logistics Callback Agent")

# Add CORS middleware to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

# Models
class TriggerCallRequest(BaseModel):
    driver_name: str
    phone_number: str
    vehicle_number: str
    destination: str

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"422 Validation Error: {exc.errors()}\nBody: {body.decode()}")
    return await request.app.default_exception_handler(request, exc)

@app.on_event("startup")
async def startup_event():
    init_db()
    scheduler.start()
    logger.info("Scheduler started")

@app.get("/config")
async def get_config():
    """Serve configuration to frontend - single source of truth from .env"""
    return {
        "bolna_api_key": BOLNA_API_KEY,
        "agent_id": AGENT_ID,
        "bolna_executions_base": f"{BOLNA_API_URL}/v2/agent",
        "bolna_execution_detail": f"{BOLNA_API_URL.replace('/v2', '')}/executions"
    }

@app.post("/create-agent")
async def create_agent_endpoint():
    url = f"{BOLNA_API_URL}/v2/agent"
    headers = {
        "Authorization": f"Bearer {BOLNA_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    # Get the system prompt with context variable placeholders
    # Bolna uses {variable_name} syntax for custom variables from user_data
    prompts = get_agent_prompts()
    
    # Ensure the task has an ID that matches the prompt key "task_1"
    config = get_agent_config()
    if config.get("tasks"):
        # Force the ID of the first task to be "task_1" to match agent_prompts
        config["tasks"][0]["id"] = "task_1"

    payload = {
        "agent_config": config,
        "agent_prompts": prompts
    }
    
    # DEBUG: Log full payload
    logger.info(f"=== AGENT CREATION PAYLOAD ===")
    logger.info(json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        new_agent_id = data.get("agent_id")
        
        # PERSIST TO .ENV FILE
        try:
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                with open(env_path, 'w') as f:
                    for line in lines:
                        if line.startswith('BOLNA_AGENT_ID='):
                            f.write(f'BOLNA_AGENT_ID={new_agent_id}\n')
                        else:
                            f.write(line)
                
                # Update in-memory variable
                global AGENT_ID
                AGENT_ID = new_agent_id
                logger.info(f"Updated .env and in-memory AGENT_ID to {new_agent_id}")
        except Exception as e:
            logger.warning(f"Could not update .env file: {e}")

        logger.info(f"Agent created: {data}")
        return {"agent_id": new_agent_id, "status": "created"}
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(f"Bolna API Error: {e.response.status_code} - {error_detail}")
        raise HTTPException(status_code=500, detail=f"Bolna API Error: {error_detail}")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-agent")
async def get_agent_endpoint():
    """Fetch the current agent configuration from Bolna to verify it's correct."""
    if not AGENT_ID:
        raise HTTPException(status_code=400, detail="AGENT_ID not found in .env")

    url = f"{BOLNA_API_URL}/v2/agent/{AGENT_ID}"
    headers = {
        "Authorization": f"Bearer {BOLNA_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Agent fetched: {data}")
        return data
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(f"Bolna API Error: {e.response.status_code} - {error_detail}")
        raise HTTPException(status_code=500, detail=f"Bolna API Error: {error_detail}")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-agent")
async def update_agent_endpoint():
    """Update the existing agent (AGENT_ID from .env) with current code/config."""
    if not AGENT_ID:
        raise HTTPException(status_code=400, detail="AGENT_ID not found in .env")

    url = f"{BOLNA_API_URL}/v2/agent/{AGENT_ID}"
    headers = {
        "Authorization": f"Bearer {BOLNA_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    prompts = get_agent_prompts()
    config = get_agent_config()
    
    # CRITICAL FIX: Ensure the task ID matches the prompt key
    # agent_prompts returns keys like "task_1", so the task must have id="task_1"
    if config.get("tasks"):
        config["tasks"][0]["id"] = "task_1"

    # IMPORTANT: Remove system_prompt from llm_config if it exists
    # Bolna expects it in agent_prompts, not in the config
    if config.get("tasks") and config["tasks"][0].get("tools_config", {}).get("llm_agent", {}).get("system_prompt"):
        del config["tasks"][0]["tools_config"]["llm_agent"]["system_prompt"]

    payload = {
        "agent_config": config,
        "agent_prompts": prompts  # This is where the prompt actually goes!
    }
    
    logger.info(f"Sending payload to Bolna with prompts: {list(prompts.keys())}")
    
    try:
        # Use PUT for updating
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Agent updated: {data}")
        return {"agent_id": data.get("agent_id"), "status": "updated", "message": "Agent updated successfully"}
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e, 'response') else str(e)
        logger.error(f"Bolna API Error: {e.response.status_code} - {error_detail}")
        raise HTTPException(status_code=500, detail=f"Bolna API Error: {error_detail}")
    except Exception as e:
        logger.error(f"Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-call")
async def trigger_call_endpoint(request: TriggerCallRequest):
    """Initiate a call to a driver."""
    logger.info(f"Received call request: {request.dict()}")
    
    call_id = f"call_{int(datetime.now().timestamp())}"
    
    trip = TripDetail(
        call_id=call_id,
        driver_name=request.driver_name,
        phone_number=request.phone_number,
        vehicle_number=request.vehicle_number,
        destination=request.destination,
        status="scheduled",
        timestamp=datetime.now().isoformat()
    )
    save_trip(trip)
    
    # Trigger call asynchronously
    await _initiate_bolna_call(trip)
    
    return {"status": "scheduled", "call_id": call_id}

async def _initiate_bolna_call(trip: TripDetail):
    """Internal function to call Bolna API."""
    url = f"{BOLNA_API_URL}/call"
    headers = {"Authorization": f"Bearer {BOLNA_API_KEY}", "Content-Type": "application/json"}
    
    # Use user_data to pass driver-specific context to the agent
    # This will be available in the conversation context
    payload = {
        "agent_id": AGENT_ID,
        "recipient_phone_number": trip.phone_number,
        "user_data": {
            "driver_name": trip.driver_name,
            "vehicle_number": trip.vehicle_number,
            "destination": trip.destination,
            "call_id": trip.call_id  # Track our internal call ID
        },
        "webhook_url": f"{os.getenv('WEBHOOK_BASE_URL', 'http://localhost:8000')}/webhook/call-completed"
    }
    
    try:
        logger.info(f"Calling {trip.phone_number} for driver {trip.driver_name} with vehicle {trip.vehicle_number}...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        # Bolna returns call_id usually
        bolna_call_id = response.json().get("call_id", "unknown")
        logger.info(f"Call initiated: {bolna_call_id}")
        
        # Update our tracking with Bolna's call ID
        trip.bolna_call_id = bolna_call_id
        update_trip_status(trip.call_id, "calling", bolna_call_id=bolna_call_id)
        
    except Exception as e:
        logger.error(f"Failed to initiate call: {e}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
        update_trip_status(trip.call_id, "failed")
        # Retry logic
        if trip.retry_count < MAX_RETRIES:
            trip.retry_count += 1
            schedule_retry(trip)

def schedule_retry(trip: TripDetail):
    retry_time = datetime.now() + timedelta(minutes=CALLBACK_RETRY_MINUTES)
    logger.info(f"Scheduling retry for {trip.call_id} at {retry_time}")
    scheduler.add_job(_initiate_bolna_call, DateTrigger(run_date=retry_time), args=[trip])

@app.post("/webhook/call-completed")
async def webhook_handler(request: Request):
    """Handle completion webhook from Bolna."""
    base_data = await request.json()
    logger.info(f"Webhook received: {json.dumps(base_data, indent=2)}")
    
    # Extract data from Bolna's payload
    bolna_call_id = base_data.get("call_id")
    status = base_data.get("status", "completed")
    user_data = base_data.get("user_data", {})
    our_call_id = user_data.get("call_id") if user_data else None
    
    # Get transcript and conversation data
    transcript = base_data.get("transcript", [])
    conversation_details = base_data.get("conversation_details", {})
    extracted_data = base_data.get("extracted_data", {})
    
    # Find the trip by our internal call_id or bolna_call_id
    trips = get_all_trips()
    matching_trip = None
    
    if our_call_id:
        matching_trip = next((t for t in trips if t.call_id == our_call_id), None)
    
    if not matching_trip and bolna_call_id:
        matching_trip = next((t for t in trips if hasattr(t, 'bolna_call_id') and t.bolna_call_id == bolna_call_id), None)
    
    if matching_trip:
        # Save complete call log with transcript and extracted data
        from database import save_call_log
        
        call_log = {
            "call_id": matching_trip.call_id,
            "bolna_call_id": bolna_call_id,
            "driver_name": matching_trip.driver_name,
            "phone_number": matching_trip.phone_number,
            "vehicle_number": matching_trip.vehicle_number,
            "destination": matching_trip.destination,
            "status": status,
            "timestamp": matching_trip.timestamp,
            "completed_at": datetime.now().isoformat(),
            "transcript": transcript,
            "conversation_details": conversation_details,
            "extracted_fields": {
                "verified_name": extracted_data.get("verified_name", ""),
                "vehicle_number_confirmed": extracted_data.get("vehicle_number_confirmed", ""),
                "current_location": extracted_data.get("current_location", ""),
                "remaining_distance": extracted_data.get("remaining_distance", ""),
                "eta_hours": extracted_data.get("eta_hours", ""),
                "delay_reason": extracted_data.get("delay_reason", ""),
                "language_chosen": extracted_data.get("language_chosen", "")
            }
        }
        
        save_call_log(call_log)
        update_trip_status(matching_trip.call_id, status, extracted_data=extracted_data, bolna_call_id=bolna_call_id)
        logger.info(f"Call log saved for {matching_trip.driver_name} (call_id: {matching_trip.call_id})")
    else:
        logger.warning(f"Could not find matching trip for call_id: {bolna_call_id}")
    
    # Handling auto-callback if busy/no-answer
    if status in ["busy", "no-answer", "failed"] and matching_trip:
        if matching_trip.retry_count < MAX_RETRIES:
            matching_trip.retry_count += 1
            schedule_retry(matching_trip)
            logger.info(f"Scheduled retry for {matching_trip.driver_name}")
    
    return {"status": "ok", "message": "Webhook processed successfully"}

@app.get("/trips")
async def get_trips():
    return get_all_trips()

@app.get("/call-logs")
async def get_all_call_logs():
    """Get call logs for all users."""
    from database import get_call_logs
    return get_call_logs()

@app.get("/call-logs/{phone_number}")
async def get_user_call_logs(phone_number: str):
    """Get call logs for a specific user by phone number."""
    from database import get_call_logs
    logs = get_call_logs(phone_number)
    if not logs:
        raise HTTPException(status_code=404, detail="No call logs found for this phone number")
    return logs

# ── Transcript JSON File Endpoints ──────────────────────────────────────────

IST = ZoneInfo("Asia/Kolkata")

# Ollama configuration for local LLM extraction
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

EXTRACTION_PROMPT = """You are given a transcript of a phone call between a logistics coordinator and a truck driver.
The conversation may be in Hindi, Marathi, Tamil, Telugu, English, or a mix of these languages.
Extract the following fields from the conversation. Return ONLY valid JSON, no explanation.

{
  "verified_name": "The driver's name as confirmed/verified during the call (or empty string if not confirmed)",
  "verified_vehicle_number": "Use the pre-filled vehicle number as ground truth. 
    During the call, the agent reads it out phonetically character by character 
    (e.g. 'bee dee seven three two six' for 'BD 7326'). 
    Do NOT re-extract the vehicle number from the phonetic spelling in the transcript. 
    Instead: if the driver confirmed it (said हाँ, yes, हम्म, or any affirmative) — 
    return the exact pre-filled value as-is. 
    If driver denied it — return the pre-filled value with a note: 'BD 7326 (not confirmed by driver)'. 
    If unclear — return the pre-filled value with note: 'BD 7326 (confirmation unclear)'. 
    Never construct a vehicle number from phonetic letters in the transcript.",
  "current_location": "The driver's current location mentioned during the call (format as 'City/Area, State' if identifiable, or empty string)",
  "distance_remaining": "Distance left to destination as mentioned by the driver (e.g. '600 km', '200 kilometers', or empty string)",
  "eta": "Estimated time of arrival — read the FULL transcript carefully and combine fragmented answers across multiple turns. A driver often says the day in one turn and the time in another turn due to natural pauses. Combine them into a single complete value. Always extract in format 'Day + Time' wherever possible — example: 'Tomorrow morning 8:30 AM', 'Today evening 6 PM', 'Day after tomorrow 10 AM'. If transcription has garbled time words like 'दशक' or 'बजे' — use context to infer the correct meaning. 'दशक' near a time context means 'बजे' (o clock). If only day is mentioned and no time despite the full transcript — write 'Tomorrow (time not specified)'. Never write just 'tomorrow' or 'today' alone.",
  "issues_faced": "Any issues/problems mentioned during the trip. If no issues, set to 'No'. If issues exist, describe them briefly (e.g. 'Tyre puncture', 'Traffic jam', 'Breakdown'). Read the FULL transcript — drivers often mention issues across multiple turns. Combine all issue mentions into one complete description."
}

IMPORTANT:
- Extract values exactly as the DRIVER (user) stated them, not what the assistant asked.
- For eta and issues_faced specifically — reason across the ENTIRE transcript, not just one turn. Drivers speak in fragments due to phone call pauses. The complete answer is often spread across 2-3 turns.
- If transcription looks garbled but context makes the meaning clear — extract the intended meaning, not the garbled text.
- If a field was asked but the driver did not give a clear answer, leave it as empty string.
- For issues_faced: if the driver said everything is fine / no issues, put "No". If they mentioned any problem, describe it.
- Return ONLY the JSON object, nothing else. No markdown, no explanation.
"""

def _parse_transcript_with_llm(transcript: str) -> Dict:
    """
    Use local Ollama (llama3.1) to extract structured fields from the call transcript.
    Connects via OpenAI-compatible API at localhost:11434.
    """
    import openai

    try:
        client = openai.OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",  # Ollama doesn't need a real key
        )
        logger.info(f"Calling Ollama ({OLLAMA_MODEL}) for transcript extraction...")
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": f"TRANSCRIPT:\n{transcript}"}
            ]
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"Ollama raw response: {raw[:300]}")
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        logger.info(f"Extraction result: {parsed}")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}\nRaw: {raw}")
        return _empty_extraction()
    except Exception as e:
        logger.error(f"LLM transcript extraction failed: {e}")
        return _empty_extraction()


def _empty_extraction() -> Dict:
    return {
        "verified_name": "",
        "verified_vehicle_number": "",
        "current_location": "",
        "distance_remaining": "",
        "eta": "",
        "issues_faced": ""
    }


def _clean_phone(phone: str) -> str:
    """Remove + and spaces from phone number for filename."""
    return re.sub(r"[^\d]", "", phone)


class SaveTranscriptRequest(BaseModel):
    """Payload sent from frontend to save a single execution's transcript."""
    execution_id: str
    status: Optional[str] = None
    created_at: Optional[str] = None
    conversation_time: Optional[float] = None
    transcript: Optional[str] = None
    extracted_data: Optional[Dict] = None
    telephony_data: Optional[Dict] = None
    cost_breakdown: Optional[Dict] = None
    error_message: Optional[str] = None
    # Pre-filled trip context (passed from frontend)
    driver_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    source_location: Optional[str] = None
    destination_location: Optional[str] = None


@app.post("/save-transcript")
async def save_transcript(payload: SaveTranscriptRequest):
    """
    Save a call's recording URL + transcript to a structured JSON file.
    Filename: {YYYY-MM-DD_HH-MM-SS_IST}_{phone_number}.json
    The datetime in the filename is the actual call time (created_at), NOT the save time.
    """
    # ── Parse the call's actual timestamp and convert to IST ──────────
    if payload.created_at:
        try:
            from dateutil import parser as dtparser
            call_dt_utc = dtparser.isoparse(payload.created_at)
            call_dt_ist = call_dt_utc.astimezone(IST)
        except Exception:
            call_dt_ist = datetime.now(IST)
    else:
        call_dt_ist = datetime.now(IST)

    phone = _clean_phone(
        (payload.telephony_data or {}).get("to_number", "unknown")
    )
    filename = f"{call_dt_ist.strftime('%Y-%m-%d_%H-%M-%S_IST')}_{phone}.json"
    file_path = TRANSCRIPTS_DIR / filename

    # ── Try to match trip data from our database ─────────────────────
    pre_filled_name = payload.driver_name or ""
    pre_filled_vehicle = payload.vehicle_number or ""
    pre_filled_source = payload.source_location or ""
    pre_filled_dest = payload.destination_location or ""

    # If pre-filled data wasn't sent from frontend, try to look it up
    if not pre_filled_name:
        to_number = _clean_phone((payload.telephony_data or {}).get("to_number", ""))
        to_suffix = to_number[-10:] if len(to_number) >= 10 else to_number
        if to_suffix:
            trips = get_all_trips()
            # Find the most recent trip matching this phone (last in list)
            matches = [
                t for t in trips
                if _clean_phone(t.phone_number)[-10:] == to_suffix
            ]
            if matches:
                match = matches[-1]  # Most recent
                pre_filled_name = match.driver_name
                pre_filled_vehicle = match.vehicle_number
                pre_filled_dest = match.destination

    # ── Extract fields from transcript via LLM ───────────────────────
    extracted = {
        "verified_name": "",
        "verified_vehicle_number": "",
        "current_location": "",
        "distance_remaining": "",
        "eta": "",
        "issues_faced": ""
    }
    if payload.transcript:
        extracted = _parse_transcript_with_llm(payload.transcript)

    # ── Build the structured JSON ────────────────────────────────────
    data = {
        "execution_id": payload.execution_id,
        "call_status": payload.status,
        "call_datetime_ist": call_dt_ist.isoformat(),
        "created_at": payload.created_at,
        "conversation_duration_seconds": payload.conversation_time,
        "recording_url": (payload.telephony_data or {}).get("recording_url"),
        "to_number": (payload.telephony_data or {}).get("to_number"),
        "from_number": (payload.telephony_data or {}).get("from_number"),

        "pre_filled": {
            "name": pre_filled_name,
            "vehicle_number": pre_filled_vehicle,
            "source_location": pre_filled_source,
            "destination_location": pre_filled_dest
        },

        "extracted_from_call": {
            "verified_name": extracted.get("verified_name", ""),
            "verified_vehicle_number": extracted.get("verified_vehicle_number", ""),
            "current_location": extracted.get("current_location", ""),
            "distance_remaining": extracted.get("distance_remaining", ""),
            "eta": extracted.get("eta", ""),
            "issues_faced": extracted.get("issues_faced", "")
        },

        "full_transcript": payload.transcript,
        "telephony_data": payload.telephony_data,
        "cost_breakdown": payload.cost_breakdown,
        "error_message": payload.error_message,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logger.info(f"Transcript saved → {file_path}")
    return {"status": "saved", "file": str(file_path), "filename": filename}


@app.get("/transcripts")
async def list_transcripts():
    """List all saved transcript JSON files."""
    files = sorted(TRANSCRIPTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)
    results = []
    for fp in files:
        with open(fp, "r") as f:
            try:
                data = json.load(f)
                results.append({
                    "file": fp.name,
                    "execution_id": data.get("execution_id"),
                    "to_number": data.get("to_number"),
                    "call_datetime_ist": data.get("call_datetime_ist"),
                    "pre_filled": data.get("pre_filled"),
                    "extracted_from_call": data.get("extracted_from_call"),
                    "has_transcript": bool(data.get("full_transcript")),
                    "has_recording": bool(data.get("recording_url")),
                })
            except json.JSONDecodeError:
                continue
    return {"total": len(results), "transcripts": results}


@app.get("/transcripts/{execution_id}")
async def get_transcript(execution_id: str):
    """Get a saved transcript by execution ID (searches all files)."""
    for fp in TRANSCRIPTS_DIR.glob("*.json"):
        with open(fp, "r") as f:
            try:
                data = json.load(f)
                if data.get("execution_id") == execution_id:
                    return data
            except json.JSONDecodeError:
                continue
    raise HTTPException(status_code=404, detail="Transcript not found")

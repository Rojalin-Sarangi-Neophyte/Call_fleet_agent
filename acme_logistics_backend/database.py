
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

DB_FILE = "acme_fleet_data.json"
CALL_LOGS_FILE = "call_logs.json"

class TripDetail(BaseModel):
    call_id: str
    driver_name: str
    phone_number: str
    vehicle_number: str
    destination: str
    status: str  # "scheduled", "completed", "failed", "busy", "no-answer", "calling"
    timestamp: str
    extracted_data: Optional[Dict] = None
    retry_count: int = 0
    bolna_call_id: Optional[str] = None

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(CALL_LOGS_FILE):
        with open(CALL_LOGS_FILE, "w") as f:
            json.dump({}, f)

def get_all_trips() -> List[TripDetail]:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return [TripDetail(**item) for item in data]
    except json.JSONDecodeError:
        return []

def save_trip(trip: TripDetail):
    trips = get_all_trips()
    # Check if exists, update
    for i, t in enumerate(trips):
        if t.call_id == trip.call_id:
            trips[i] = trip
            _write_db(trips)
            return
    # Else append
    trips.append(trip)
    _write_db(trips)

def _write_db(trips: List[TripDetail]):
    with open(DB_FILE, "w") as f:
        json.dump([t.dict() for t in trips], f, indent=4)

def update_trip_status(call_id: str, status: str, extracted_data: Dict = None, bolna_call_id: str = None):
    trips = get_all_trips()
    for t in trips:
        if t.call_id == call_id:
            t.status = status
            if extracted_data:
                t.extracted_data = extracted_data
            if bolna_call_id:
                t.bolna_call_id = bolna_call_id
            _write_db(trips)
            return

def save_call_log(call_log: Dict):
    """Save complete call log with transcript and extracted fields per user."""
    # Load existing logs
    if os.path.exists(CALL_LOGS_FILE):
        with open(CALL_LOGS_FILE, "r") as f:
            try:
                all_logs = json.load(f)
            except json.JSONDecodeError:
                all_logs = {}
    else:
        all_logs = {}
    
    # Use phone number as key to group all calls for a user
    phone_number = call_log.get("phone_number", "unknown")
    
    # Initialize user's call history if not exists
    if phone_number not in all_logs:
        all_logs[phone_number] = {
            "driver_name": call_log.get("driver_name"),
            "phone_number": phone_number,
            "calls": []
        }
    
    # Add this call to user's history
    all_logs[phone_number]["calls"].append(call_log)
    
    # Write back to file
    with open(CALL_LOGS_FILE, "w") as f:
        json.dump(all_logs, f, indent=4)

def get_call_logs(phone_number: Optional[str] = None) -> Dict:
    """Get call logs for a specific user or all users."""
    if not os.path.exists(CALL_LOGS_FILE):
        return {}
    
    with open(CALL_LOGS_FILE, "r") as f:
        try:
            all_logs = json.load(f)
        except json.JSONDecodeError:
            return {}
    
    if phone_number:
        return all_logs.get(phone_number, {})
    
    return all_logs

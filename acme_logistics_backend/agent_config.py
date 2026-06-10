SYSTEM_PROMPT = """
You are Anh, a trip coordinator at ACME Logistics. You are calling a delivery driver for a trip update. You sound warm, natural, and professional.

## CRITICAL — LANGUAGE CONTROL
1. YOU MUST CONDUCT THE CALL IN ONLY ONE LANGUAGE once confirmed.
2. If the driver chooses Vietnamese, NEVER speak English again.
3. If the driver speaks Vietnamese, respond ONLY in Vietnamese.
4. The instructions below provide both Vietnamese and English variants. Use ONLY the variant for the confirmed language.

## WHO YOU ARE
Name: Anh. Role: Trip Coordinator at ACME Logistics. 

## WHAT YOU ALREADY KNOW
- Driver Name: {driver_name}
- Vehicle Number: {vehicle_number}
- Destination: {destination}

## CONVERSATION FLOW & STEPS
Follow these 7 steps in order. Advance only when you have a clear answer. If an answer is ambiguous, ask ONE time to clarify, then move forward regardless.

### FIRST TURN — LANGUAGE SELECTION
The call starts with the message "Xin chào từ ACME Logistics!".
Your very first turn MUST BE:
"Xin chào! Tôi là Anh từ ACME Logistics. Bạn muốn nói chuyện bằng ngôn ngữ nào — tiếng Việt hay tiếng Anh?"

- If "Vietnamese": Switch to Vietnamese and move to Step 1.
- If "English": Switch to English and move to Step 1.
- If unclear: Ask once "Bạn thích nói chuyện bằng ngôn ngữ nào hơn?" If still unclear, default to Vietnamese.

### STEP 1 — NAME VERIFICATION
- Vietnamese: "Tôi đang nói chuyện với {driver_name} phải không?"
- English: "Am I speaking with {driver_name}?"
Reaction: Acknowledge briefly ("Được rồi, {driver_name}" / "Alright, {driver_name}") and move to Step 2.

### STEP 2 — VEHICLE NUMBER
The vehicle number is {vehicle_number}.
RULE: Characters (letters/numbers) MUST be spoken in English even in a Vietnamese sentence.
Spelling: {vehicle_number} -> [spell letters and digits individually in English].

- Vietnamese: "Số xe của bạn là [English spelling] — đúng không?"
- English: "Your vehicle number is [English spelling] — correct?"
If YES: Move to Step 3.

### STEP 3 — CURRENT LOCATION
- Vietnamese: "Hiện tại bạn đang ở đâu? Vị trí của bạn là gì?"
- English: "Where are you right now?"
Confirmation: Briefly confirm ("Đã rõ, tại [location]" / "Got it, [location]") and immediately ask Step 4.

### STEP 4 — REMAINING DISTANCE
- Vietnamese: "Còn bao nhiêu xa nữa thì đến nơi?"
- English: "How much distance is left to the destination?"

### STEP 5 — ETA
- Vietnamese: "Khoảng mấy giờ bạn dự kiến sẽ đến?"
- English: "What time do you expect to arrive roughly?"

### STEP 6 — TRIP STATUS
- Vietnamese: "Chuyến đi ổn chứ? Có vấn đề gì đặc biệt không?"
- English: "Is the trip going smoothly? Any issues?"
Note: If there is an issue (hỏng xe, chậm trễ, tắc đường), acknowledge empathetically before moving to Step 7.

### STEP 7 — FINAL QUESTION
- Vietnamese: "Bạn có câu hỏi nào về chuyến đi không?"
- English: "Any questions about the trip?"
- If they have a question: "Được rồi, tôi sẽ kết nối bạn với đội ngũ." (Use transfer_call tool).
- If no: "Cảm ơn {driver_name}! Chúc bạn thượng lộ bình an và hãy cẩn thận nhé!" (Use save_trip_details tool).

## COMPLIANCE RULES
- NEVER repeat the driver's answer back to them verbatim.
- ONE short reaction per turn maximum (Được rồi, Đã rõ, Rất tốt, Okay).
- NO filler stacking (e.g., "Vâng, chắc chắn, được rồi").
- Use commas to create natural pauses for the voice engine.
- If the driver shares info out of order, acknowledge it and skip that step later.
- After goodbye, if the driver speaks again, say: "Thông tin của bạn đã được ghi lại. Chúc bạn thượng lộ bình an!" then stop.

## ADVANCEMENT LOGIC
Before every response, check:
1. Did the driver answer my last question?
2. If YES: React and ask the NEXT step's question.
3. If NO: Rephrase the current question simply.
4. Do not repeat the same question more than twice. If still no answer, move to the next step.
"""



def get_agent_config(agent_name="FM_fleet_manager_vietnamese"):
    # Minimal Working Configuration
    return {
        "agent_name": "FM_fleet_manager_vietnamese_v4",
        "agent_type": "other",
        "agent_welcome_message": "Xin chào từ ACME Logistics!",
        "tasks": [
            {
                "id": "task_1",
                "task_type": "conversation",
                "toolchain": {
                    "execution": "parallel",
                    "pipelines": [["transcriber", "llm", "synthesizer"]]
                },
                "tools_config": {
                    "input": {
                        "format": "wav",
                        "provider": "plivo"
                    },
                    "output": {
                        "format": "wav",
                        "provider": "plivo"
                    },
                    "transcriber": {
                        "provider": "openai",
                        "model": "GPT Realtime Whisper",
                        "language": "vi",
                        "stream": True,
                        "sampling_rate": 16000,
                        "encoding": "linear16",
                        "endpointing": 420
                    },
                    "llm_agent": {
                        "agent_type": "simple_llm_agent",
                        "agent_flow_type": "streaming",
                        "llm_config": {
                            "provider": "openai",
                            "family": "openai",
                            "model": "gpt-4o",
                            "temperature": 0.75,
                            "max_tokens": 150,
                            "top_p": 0.9,
                            "presence_penalty": 0.65,
                            "frequency_penalty": 0.65,
                            "base_url": "https://api.openai.com/v1"
                        },
                        "system_prompt": SYSTEM_PROMPT
                    },
                    "synthesizer": {
                        "provider": "elevenlabs",
                        "provider_config": {
                            "voice": "Drew - Crisp, Clear and Balanced",
                            "voice_id": "Qdoacjdd3OKJ1mMc318A",
                            "model": "eleven_multilingual_v2",
                            "stability": 0.6,
                            "similarity_boost": 0.9,
                            "style": 1.0,
                            "use_speaker_boost": True,
                            "speed": 0.94
                        },
                        "stream": True,
                        "buffer_size": 160,
                        "audio_format": "wav"
                    }
                },
                "task_config": {
                    "hangup_after_silence": 45,
                    "incremental_delay": 300,
                    "ambient_noise": False,
                    "backchanneling": False,
                    "generate_precise_transcript": False,
                    "use_llm_for_initial_message": True,
                    "voicemail": False,
                    "voicemail_detection_time": 0,
                    "check_if_user_online": False,
                    "call_terminate": 300
                }
            }
        ]
    }
def get_agent_prompts():
    """Return the system prompt with context variable placeholders.
    
    The actual values for {driver_name}, {vehicle_number}, and {destination}
    will be injected by Bolna at runtime from the user_data field passed 
    in the /call API payload.
    
    Bolna uses SINGLE curly braces {} for custom variables from user_data.
    """
    return {
        "task_1": {
            "system_prompt": SYSTEM_PROMPT
        }
    }

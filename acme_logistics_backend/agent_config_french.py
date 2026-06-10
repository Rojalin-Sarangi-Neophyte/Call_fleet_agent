SYSTEM_PROMPT = """
You are Aaron, a trip coordinator at ACME Logistics. You are calling a delivery driver for a trip update. You sound warm, natural, and professional.

## CRITICAL — LANGUAGE CONTROL
1. YOU MUST CONDUCT THE CALL IN ONLY ONE LANGUAGE once confirmed.
2. If the driver chooses French, NEVER speak English again.
3. If the driver speaks French, respond ONLY in French.
4. The instructions below provide both French and English variants. Use ONLY the variant for the confirmed language.

## WHO YOU ARE
Name: Aaron. Role: Trip Coordinator at ACME Logistics. 

## WHAT YOU ALREADY KNOW
- Driver Name: {driver_name}
- Vehicle Number: {vehicle_number}
- Destination: {destination}

## CONVERSATION FLOW & STEPS
Follow these 7 steps in order. Advance only when you have a clear answer. If an answer is ambiguous, ask ONE time to clarify, then move forward regardless.

### FIRST TURN — LANGUAGE SELECTION
The call starts with the message "Bonjour de la part de ACME Logistics !".
Your very first turn MUST BE:
"Bonjour ! Je suis Aaron de ACME Logistics. Dans quelle langue souhaitez-vous parler — français ou anglais ?"

- If "Français": Switch to French and move to Step 1.
- If "English": Switch to English and move to Step 1.
- If unclear: Ask once "Dans quelle langue préférez-vous parler ?" If still unclear, default to French.

### STEP 1 — NAME VERIFICATION
- French: "Est-ce que je parle bien à {driver_name} ?"
- English: "Am I speaking with {driver_name}?"
Reaction: Acknowledge briefly ("D'accord, {driver_name}" / "Alright, {driver_name}") and move to Step 2.

### STEP 2 — VEHICLE NUMBER
The vehicle number is {vehicle_number}.
RULE: Characters (letters/numbers) MUST be spoken in English even in a French sentence.
Spelling: {vehicle_number} -> [spell letters and digits individually in English].

- French: "Votre numéro de véhicule est [English spelling] — c'est bien ça ?"
- English: "Your vehicle number is [English spelling] — correct?"
If YES: Move to Step 3.

### STEP 3 — CURRENT LOCATION
- French: "Où êtes-vous actuellement ? Quelle est votre position ?"
- English: "Where are you right now?"
Confirmation: Briefly confirm ("Entendu, à [location]" / "Got it, [location]") and immediately ask Step 4.

### STEP 4 — REMAINING DISTANCE
- French: "Quelle distance reste-t-il jusqu'à la destination ?"
- English: "How much distance is left to the destination?"

### STEP 5 — ETA
- French: "À quelle heure environ prévoyez-vous d'arriver ?"
- English: "What time do you expect to arrive roughly?"

### STEP 6 — TRIP STATUS
- French: "Le trajet se passe bien ? Pas de souci particulier ?"
- English: "Is the trip going smoothly? Any issues?"
Note: If there is an issue (panne, retard, trafic), acknowledge empathetically before moving to Step 7.

### STEP 7 — FINAL QUESTION
- French: "Avez-vous des questions sur le trajet ?"
- English: "Any questions about the trip?"
- If they have a question: "D'accord, je vous mets en relation avec l'équipe." (Use transfer_call tool).
- If no: "Merci, {driver_name} ! Bonne route et faites attention à vous !" (Use save_trip_details tool).

## COMPLIANCE RULES
- NEVER use "tu" in French. Always use "vous".
- NEVER repeat the driver's answer back to them verbatim.
- ONE short reaction per turn maximum (D'accord, Entendu, Très bien, Okay).
- NO filler stacking (e.g., "Oui, absolument, d'accord").
- Use commas to create natural pauses for the voice engine.
- If the driver shares info out of order, acknowledge it and skip that step later.
- After goodbye, if the driver speaks again, say: "Vos informations sont enregistrées. Bonne route !" then stop.

## ADVANCEMENT LOGIC
Before every response, check:
1. Did the driver answer my last question?
2. If YES: React and ask the NEXT step's question.
3. If NO: Rephrase the current question simply.
4. Do not repeat the same question more than twice. If still no answer, move to the next step.
"""



def get_agent_config(agent_name="FM_fleet_manager_02"):
    # Minimal Working Configuration
    return {
        "agent_name": agent_name,
        "agent_type": "other",
        "agent_welcome_message": "Bonjour de la part de ACME Logistics !",
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
                        "provider": "deepgram",
                        "model": "nova-2",
                        "language": "fr",
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
                    "hangup_after_silence": 45,  # Increased to give more time for final question
                    "incremental_delay": 300,
                    "ambient_noise": False,
                    "backchanneling": False,
                    "generate_precise_transcript": False,
                    "use_llm_for_initial_message": True,
                    "voicemail": False,
                    "voicemail_detection_time": 0,
                    "check_if_user_online": False,
                    "call_terminate": 300  # 5 minutes max call duration
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

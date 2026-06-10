# AGENT CONFIGURATION PARAMETERS GUIDE

# Complete reference for all parameters in get_agent_config()

## ROOT LEVEL PARAMETERS

### agent_name

- **Type:** String
- **Current:** "Acme_fleet_manager_01"
- **Purpose:** Identifier for your agent in Bolna dashboard
- **Effect:** Display name only, doesn't affect behavior

### agent_type

- **Type:** String
- **Current:** "other"
- **Options:** "other", "sales", "support", "custom"
- **Purpose:** Categorization for analytics
- **Effect:** No behavioral impact, just for organization

---

## TASK CONFIGURATION

### id

- **Type:** String
- **Current:** "task_1"
- **Purpose:** Links task to prompts in agent_prompts
- **Effect:** MUST match the key in get_agent_prompts() or prompt won't load
- **Critical:** Don't change unless you also change agent_prompts key

### task_type

- **Type:** String
- **Current:** "conversation"
- **Options:** "conversation", "webhook", "transfer"
- **Purpose:** Defines what the agent does
- **Effect:** "conversation" = voice call with LLM

---

## TOOLCHAIN CONFIGURATION

### execution

- **Type:** String
- **Current:** "parallel"
- **Options:** "parallel", "sequential"
- **Purpose:** How tools run (transcriber → LLM → synthesizer)
- **Effect:**
  - "parallel" = Faster, streams audio while processing
  - "sequential" = Slower, waits for each step to complete

### pipelines

- **Type:** Array of arrays
- **Current:** [["transcriber", "llm", "synthesizer"]]
- **Purpose:** Defines the flow of data processing
- **Effect:** Order matters! Don't change unless you know what you're doing

---

## INPUT/OUTPUT CONFIGURATION

### input.format

- **Type:** String
- **Current:** "wav"
- **Purpose:** Audio format from phone provider
- **Effect:** Must match Plivo's output format

### input.provider

- **Type:** String
- **Current:** "plivo"
- **Purpose:** Telephony provider for incoming audio
- **Effect:** Must match your Bolna account telephony setup

### output.format

- **Type:** String
- **Current:** "wav"
- **Purpose:** Audio format to phone provider
- **Effect:** Must match Plivo's input format

### output.provider

- **Type:** String
- **Current:** "plivo"
- **Purpose:** Telephony provider for outgoing audio
- **Effect:** Must match your Bolna account telephony setup

---

## TRANSCRIBER (SPEECH-TO-TEXT) CONFIGURATION

### transcriber.provider

- **Type:** String
- **Current:** "deepgram"
- **Options:** "deepgram", "whisper", "google", "azure"
- **Purpose:** Which STT service to use
- **Effect:** Accuracy and speed vary by provider

### transcriber.model

- **Type:** String
- **Current:** "nova-2"
- **Options:** "nova-2", "nova", "base", "enhanced"
- **Purpose:** Deepgram model version
- **Effect:**
  - "nova-2" = Latest, most accurate
  - "nova" = Fast, good accuracy
  - "base" = Fastest, lower accuracy

### transcriber.language

- **Type:** String
- **Current:** "hi"
- **Options:** "hi" (Hindi), "en" (English), "mr" (Marathi), etc.
- **Purpose:** Primary language for transcription
- **Effect:** Better accuracy for the specified language

### transcriber.stream

- **Type:** Boolean
- **Current:** True
- **Purpose:** Enable real-time streaming transcription
- **Effect:**
  - True = Lower latency, faster responses
  - False = Waits for complete utterance

### transcriber.sampling_rate

- **Type:** Integer
- **Current:** 16000
- **Options:** 8000, 16000, 44100, 48000
- **Purpose:** Audio quality (Hz)
- **Effect:**
  - 16000 = Standard for phone calls (recommended)
  - 8000 = Lower quality, smaller bandwidth
  - Higher = Better quality, more bandwidth

### transcriber.encoding

- **Type:** String
- **Current:** "linear16"
- **Options:** "linear16", "mulaw", "alaw"
- **Purpose:** Audio encoding format
- **Effect:** Must match telephony provider's format

### transcriber.endpointing

- **Type:** Integer (milliseconds)
- **Current:** 250
- **Purpose:** How long to wait for silence before considering speech complete
- **Effect:**
  - Lower (100-200) = Faster responses, may cut off slow speakers
  - Higher (300-500) = More patient, may feel sluggish
  - **Recommended:** 250-300 for Indian speakers

---

## LLM AGENT CONFIGURATION

### llm_agent.agent_type

- **Type:** String
- **Current:** "simple_llm_agent"
- **Options:** "simple_llm_agent", "function_calling_agent"
- **Purpose:** Type of LLM interaction
- **Effect:** "simple_llm_agent" = Basic conversation

### llm_agent.agent_flow_type

- **Type:** String
- **Current:** "streaming"
- **Options:** "streaming", "batch"
- **Purpose:** How LLM generates responses
- **Effect:**
  - "streaming" = Words come out as generated (faster, more natural)
  - "batch" = Waits for complete response (slower)

### llm_config.provider

- **Type:** String
- **Current:** "openai"
- **Options:** "openai", "anthropic", "groq", "together"
- **Purpose:** Which LLM provider to use
- **Effect:** Different models, pricing, capabilities

### llm_config.family

- **Type:** String
- **Current:** "openai"
- **Purpose:** Model family within provider
- **Effect:** Groups similar models together

### llm_config.model

- **Type:** String
- **Current:** "gpt-4o"
- **Options:** "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
- **Purpose:** Specific model to use
- **Effect:**
  - "gpt-4o" = Smartest, best for complex conversations
  - "gpt-4-turbo" = Fast, good quality
  - "gpt-3.5-turbo" = Fastest, cheaper, less capable

### llm_config.temperature

- **Type:** Float (0.0 - 2.0)
- **Current:** 0.3
- **Purpose:** Randomness/creativity of responses
- **Effect:**
  - 0.0 = Deterministic, same response every time
  - 0.3 = Slightly varied, consistent (RECOMMENDED for agents)
  - 1.0 = More creative, less predictable
  - 2.0 = Very random, may go off-script

### llm_config.max_tokens

- **Type:** Integer
- **Current:** 150
- **Purpose:** Maximum response length
- **Effect:**
  - Lower (50-100) = Short, concise responses
  - 150 = Good for conversational turns (RECOMMENDED)
  - Higher (300+) = Longer responses, may ramble

### llm_config.top_p

- **Type:** Float (0.0 - 1.0)
- **Current:** 0.9
- **Purpose:** Nucleus sampling (alternative to temperature)
- **Effect:**
  - 0.9 = Balanced, natural variety
  - 1.0 = Consider all possibilities
  - Lower = More focused, less variety

### llm_config.min_p

- **Type:** Float (0.0 - 1.0)
- **Current:** 0.1
- **Purpose:** Minimum probability threshold
- **Effect:**
  - 0.1 = Filters out very unlikely words
  - Higher = More conservative word choices

### llm_config.presence_penalty

- **Type:** Float (-2.0 - 2.0)
- **Current:** 0
- **Purpose:** Penalize repeating topics
- **Effect:**
  - 0 = No penalty (RECOMMENDED for structured conversations)
  - Positive = Encourages new topics
  - Negative = Encourages staying on topic

### llm_config.frequency_penalty

- **Type:** Float (-2.0 - 2.0)
- **Current:** 0
- **Purpose:** Penalize repeating exact words
- **Effect:**
  - 0 = No penalty (RECOMMENDED)
  - Positive = Reduces repetition
  - Negative = May repeat more

### llm_config.base_url

- **Type:** String
- **Current:** "https://api.openai.com/v1"
- **Purpose:** API endpoint for LLM
- **Effect:** Change only if using custom/proxy endpoint

---

## SYNTHESIZER (TEXT-TO-SPEECH) CONFIGURATION

### synthesizer.provider

- **Type:** String
- **Current:** "elevenlabs"
- **Options:** "elevenlabs", "deepgram", "polly", "azure", "sarvam"
- **Purpose:** Which TTS service to use
- **Effect:** Voice quality, language support vary

### synthesizer.provider_config.voice

- **Type:** String
- **Current:** "Raju - Relatable Indian Voice"
- **Purpose:** Display name of voice
- **Effect:** Descriptive only

### synthesizer.provider_config.voice_id

- **Type:** String
- **Current:** "3gsg3cxXyFLcGIfNbM6C"
- **Purpose:** Unique identifier for the voice
- **Effect:** CRITICAL - determines which voice is used

### synthesizer.provider_config.model

- **Type:** String
- **Current:** "eleven_multilingual_v2"
- **Options:** "eleven_multilingual_v2", "eleven_turbo_v2_5", "eleven_monolingual_v1"
- **Purpose:** ElevenLabs model version
- **Effect:**
  - "eleven_multilingual_v2" = Best for Hindi/multilingual
  - "eleven_turbo_v2_5" = Fastest, good quality
  - "eleven_monolingual_v1" = English only, high quality

### synthesizer.provider_config.stability

- **Type:** Float (0.0 - 1.0)
- **Current:** 0.5
- **Purpose:** Voice consistency vs. expressiveness
- **Effect:**
  - 0.0 = Very expressive, may sound unstable
  - 0.5 = Balanced (RECOMMENDED)
  - 1.0 = Very stable, may sound monotone

### synthesizer.provider_config.similarity_boost

- **Type:** Float (0.0 - 1.0)
- **Current:** 0.75
- **Purpose:** How closely to match the original voice
- **Effect:**
  - 0.0 = More variation, may sound different
  - 0.75 = Good match (RECOMMENDED)
  - 1.0 = Exact match, may sound robotic

### synthesizer.provider_config.style

- **Type:** Float (0.0 - 1.0)
- **Current:** 0.3
- **Purpose:** Exaggeration/emphasis in speech
- **Effect:**
  - 0.0 = Flat, neutral delivery
  - 0.3 = Subtle expressiveness (RECOMMENDED)
  - 1.0 = Very dramatic, exaggerated

### synthesizer.provider_config.use_speaker_boost

- **Type:** Boolean
- **Current:** True
- **Purpose:** Enhance voice clarity
- **Effect:**
  - True = Clearer, more distinct voice (RECOMMENDED)
  - False = Natural, may be less clear

### synthesizer.provider_config.speed

- **Type:** Float (0.25 - 4.0)
- **Current:** 0.95
- **Purpose:** Speech rate
- **Effect:**
  - 0.5 = Very slow
  - 0.95 = Slightly slower than normal (RECOMMENDED for clarity)
  - 1.0 = Normal speed
  - 1.5 = Fast
  - 2.0+ = Very fast, hard to understand

### synthesizer.stream

- **Type:** Boolean
- **Current:** True
- **Purpose:** Stream audio as it's generated
- **Effect:**
  - True = Lower latency (RECOMMENDED)
  - False = Wait for complete audio

### synthesizer.buffer_size

- **Type:** Integer (bytes)
- **Current:** 250
- **Purpose:** Audio buffer size for streaming
- **Effect:**
  - Lower (100-150) = Faster start, may have gaps
  - 250 = Balanced (RECOMMENDED)
  - Higher (400+) = Smoother, more latency

### synthesizer.audio_format

- **Type:** String
- **Current:** "wav"
- **Purpose:** Output audio format
- **Effect:** Must match telephony provider requirements

---

## TASK CONFIG (CALL BEHAVIOR)

### task_config.hangup_after_silence

- **Type:** Integer (seconds)
- **Current:** 30
- **Purpose:** Hang up if user silent for this long
- **Effect:**
  - Lower (10-20) = Hangs up quickly, may be abrupt
  - 30 = Patient (RECOMMENDED)
  - Higher (60+) = Very patient, may waste time

### task_config.incremental_delay

- **Type:** Integer (milliseconds)
- **Current:** 400
- **Purpose:** Delay between audio chunks
- **Effect:**
  - Lower (200-300) = Faster, may sound rushed
  - 400 = Natural pacing (RECOMMENDED)
  - Higher (600+) = Slower, more deliberate

### task_config.ambient_noise

- **Type:** Boolean
- **Current:** False
- **Purpose:** Add background noise to sound more natural
- **Effect:**
  - True = Adds office/ambient sounds
  - False = Clean audio (RECOMMENDED)

### task_config.backchanneling

- **Type:** Boolean
- **Current:** False
- **Purpose:** Agent says "mm-hmm", "okay" while listening
- **Effect:**
  - True = More natural, may interrupt
  - False = Silent listening (RECOMMENDED for Hindi)

### task_config.generate_precise_transcript

- **Type:** Boolean
- **Current:** False
- **Purpose:** Generate detailed transcript with timestamps
- **Effect:**
  - True = Better analytics, more processing
  - False = Basic transcript (RECOMMENDED)

### task_config.use_llm_for_initial_message

- **Type:** Boolean
- **Current:** False
- **Purpose:** Let LLM generate first message vs. static welcome
- **Effect:**
  - True = Dynamic greeting based on context
  - False = Uses agent_welcome_message (RECOMMENDED for consistency)

### task_config.voicemail

- **Type:** Boolean
- **Current:** False
- **Purpose:** Detect and handle voicemail
- **Effect:**
  - True = Leaves message if voicemail detected
  - False = Treats voicemail as person (RECOMMENDED)

### task_config.voicemail_detection_time

- **Type:** Integer (seconds)
- **Current:** 0
- **Purpose:** How long to wait to detect voicemail
- **Effect:**
  - 0 = Disabled (RECOMMENDED)
  - Higher = More time to detect, more delay

### task_config.check_if_user_online

- **Type:** Boolean
- **Current:** False
- **Purpose:** Ask "Are you still there?" if silent
- **Effect:**
  - True = Prompts user if quiet
  - False = Waits silently (RECOMMENDED)

---

## RECOMMENDED SETTINGS FOR INDIAN DRIVERS

```python
# OPTIMAL CONFIGURATION
transcriber.endpointing: 250-300  # Patient for Hindi speakers
llm_config.temperature: 0.3       # Consistent, on-script
llm_config.max_tokens: 150        # Concise responses
synthesizer.speed: 0.95           # Slightly slower for clarity
synthesizer.stability: 0.5        # Balanced
synthesizer.similarity_boost: 0.75 # Natural but clear
synthesizer.style: 0.3            # Subtle expressiveness
synthesizer.buffer_size: 250      # Smooth streaming
task_config.hangup_after_silence: 30  # Patient
task_config.incremental_delay: 400    # Natural pacing
```

---

## CRITICAL PARAMETERS (DON'T CHANGE)

- `task.id` - Must match agent_prompts key
- `input/output.provider` - Must match Bolna account
- `transcriber.language` - Must match primary language
- `synthesizer.voice_id` - Determines voice quality
- `llm_config.model` - Affects intelligence/cost

## TUNING PARAMETERS (SAFE TO ADJUST)

- `transcriber.endpointing` - Adjust for speaker pace
- `llm_config.temperature` - Adjust for creativity
- `synthesizer.speed` - Adjust for clarity
- `synthesizer.stability/similarity/style` - Adjust for naturalness
- `task_config.hangup_after_silence` - Adjust for patience

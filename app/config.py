SAMPLE_RATE = 22050

# max time allowed for an LLM response
LLM_TIMEOUT_SECONDS = 120

# max time allowed for a single speech-generation/playback segment
TTS_SEGMENT_TIMEOUT_SECONDS = 45

# max number of consecutive empty or unrecognized turns
MAX_EMPTY_TURNS = 5

# time between live transcription updates
PARTIAL_TRANSCRIPTION_INTERVAL = 1.2

# max queued speech segments
MAX_AUDIO_QUEUE_SIZE = 3
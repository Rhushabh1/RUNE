# RUNE

Real-time Unified Neural Entity

Personal AI Voice Assistant

# Milestones

- short-term conversational memory
- simple tool calling - date & knowledge search
- logs, latency measurements, basic automated tests
- (optional) FastAPI backend with health checks and metrics

# Current Limitations

- fixed 5 second recording
- manual enter key for audio input
- whisper transcription
- sequential processing: STT -> LLM -> TTS
- pyttsx3 playback - no interruption or barge-in
- basic transformer LLM
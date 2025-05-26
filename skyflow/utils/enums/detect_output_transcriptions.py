from enum import Enum

class DetectOutputTranscriptions(Enum):
    DIARIZED_TRANSCRIPTION = "diarized_transcription"
    MEDICAL_DIARIZED_TRANSCRIPTION = "medical_diarized_transcription"
    MEDICAL_TRANSCRIPTION = "medical_transcription"
    PLAINTEXT_TRANSCRIPTION = "plaintext_transcription"
    TRANSCRIPTION = "transcription"
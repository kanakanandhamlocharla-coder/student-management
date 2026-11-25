import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key,http_options=types.HttpOptions(
        api_version="v1alpha"))

MODEL="gemini-3.8-live"
LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {}
}
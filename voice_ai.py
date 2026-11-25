import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

system_instruction = """
    You are a voice-command interpreter for a Student Management System.

    Understand the user's command and return ONLY valid JSON.

    Supported commands:

    1. Search by student name:
    {
        "valid": true,
        "action": "search_by_name",
        "value": "Ravi Kumar"
    }

    2. Search by exact roll number:
    {
        "valid": true,
        "action": "search_by_roll_number",
        "value": "STU-0025"
    }

    If the command is unclear or unrelated to student management, return:

    {
        "valid": false,
        "action": "unclear",
        "value": null
    }

    Rules:
    - Understand commands in English and Telugu.
    - Understand Telugu written in Telugu script and Telugu written using English letters.
    - Understand mixed English and Telugu sentences.
    - Extract the original student name or roll number accurately.
    - Translate the meaning of the command if necessary, but do not translate student names or roll numbers.
    - Return the same JSON structure regardless of the language used.
    """

def gemini(transcript):

    try:
        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=transcript,
            system_instruction=system_instruction
        )
    except Exception as error:
        print("Gemini API Error:", error)
        return {
            "valid": False,
            "action": "service_error",
            "value": None
        }

    response =  interaction.output_text.strip()
    print("Raw Gemini Response:", response)

    try:
        command = json.loads(response)

    except json.JSONDecodeError:
        return {
            "valid": False,
            "action": "unclear",
            "value": None
        }

    if not isinstance(command, dict):
        return {
            "valid": False,
            "action": "unclear",
            "value": None
        }

    action = command["action"]
    value = command["value"]

    if(
        command.get("valid") is True and
        action in ["search_by_name", "search_by_roll_number"] and
        isinstance(value, str) and value.strip()
    ):
        return command

    return {
        "valid": False,
        "action": "unclear",
        "value": None
    }

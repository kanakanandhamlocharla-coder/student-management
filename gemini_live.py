import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key, http_options=types.HttpOptions(
        api_version="v1beta"))
MODEL = "gemini-3.8-live"


search_student_tool = {
    "name": "search_student",
    "description": "Search for a student using their name.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "keyword": {
                        "type": "STRING",
                        "description": "Name of the student to search for."
                    }
        },
        "required": ["keyword"]
    }
}

get_students_statistics_tool = {
    "name": "get_student_statistics",
    "description": "Get overall student management statistics, including total students, total courses, average marks, and highest marks.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

get_course_statistics_tool = {
    "name": "get_course_statistics",
    "description": "Get overall course statistics including number of students in individual courses",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

add_student_tool = {
    "name": "add_student",
    "description": "Register a new student in the student management system.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "roll_number": {
                "type": "STRING",
                "description": "Unique roll number of the student."
            },
            "name": {
                "type": "STRING",
                "description": "Full name of the student."
            },
            "age": {
                "type": "INTEGER",
                "description": "Age of the student."
            },
            "course": {
                "type": "STRING",
                "description": "Course of the student."
            },
            "marks": {
                "type": "NUMBER",
                "description": "Marks obtained by the student."
            }
        },
        "required": ["roll_number", "name", "age", "course", "marks"]
    }
}

confirm_student_tool = {
    "name": "confirm_student_registration",
    "description": "Confirm or cancel a pending student registration. Call this only after the user explicitly says yes or no to the registration confirmation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "confirmed": {
                "type": "BOOLEAN",
                "description": "True if the user approves registration, False if the user rejects it."
            }
        },
        "required": ["confirmed"]
    }
}

prepare_student_deletion_tool = {
    "name": "prepare_student_deletion",
    "description": "Find a student by name or roll number to prepare for deletion. Never delete the student directly. The user must confirm the deletion first.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "keyword": {
                "type": "STRING",
                "description": "The student's name or roll number."
            }
        },
        "required": ["keyword"]
    }
}

confirm_student_deletion_tool = {
    "name": "confirm_student_deletion",
    "description": "Confirm or cancel a pending student deletion. Call this only after the user explicitly approves or rejects the deletion.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "confirmed": {
                "type": "BOOLEAN",
                "description": "True if the user approves deletion, False if the user rejects it."
            }
        },
        "required": ["confirmed"]
    }
}

prepare_student_update_tool = {
    "name": "prepare_student_update",
    "description": (
        "Prepare changes to an existing student's details. "
        "Use the student's ID and include only the fields the user wants to change. "
        "Never update the database directly. The user must confirm the changes first."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "student_id": {
                "type": "STRING",
                "description": "ID of the student to update."
            },
            "updates": {
                "type": "OBJECT",
                "properties": {
                    "roll_number": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "age": {"type": "INTEGER"},
                    "course": {"type": "STRING"},
                    "marks": {"type": "NUMBER"}
                }
            }
        },
        "required": ["student_id", "updates"]
    }
}

confirm_student_update_tool = {
    "name": "confirm_student_update",
    "description": (
        "Confirm or cancel a pending student update. "
        "Call this only after the user explicitly approves or rejects the changes."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "confirmed": {
                "type": "BOOLEAN",
                "description": "True if the user approves the update, False if the user rejects it."
            }
        },
        "required": ["confirmed"]
    }
}




LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
    "output_audio_transcription": {},
    "tools": [
        {
            "function_declarations": [
                search_student_tool,
                get_students_statistics_tool,
                get_course_statistics_tool,
                add_student_tool,
                confirm_student_tool,
                prepare_student_deletion_tool,
                confirm_student_deletion_tool,
                prepare_student_update_tool,
                confirm_student_update_tool,
            ]
        }
    ]
}
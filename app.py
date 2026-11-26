import asyncio
import json

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.genai import types
from mysql.connector.errors import IntegrityError
from pydantic import BaseModel, Field

from gemini_live import client, MODEL, LIVE_CONFIG
from student_repository import get_students_from_database, add_student_to_database, update_student_in_database, \
    update_student_fields_in_database, delete_student_from_database, search_student_from_database, get_dashboard_stats, get_course_distribution



class StudentCreate(BaseModel):
    roll_number: str = Field(min_length=3, max_length=30)
    name: str = Field(min_length=3, max_length=20)
    age: int = Field(gt=0)
    course: str = Field(min_length=3, max_length=20)
    marks: float = Field(ge=0, le=100)

class StudentUpdate(BaseModel):
    roll_number:str | None = None
    name:str | None = None
    age:int | None = Field(default=None, gt=0)
    course:str | None = None
    marks:float | None = Field(default=None, gt=0, le=100)


class VoiceCommandRequest(BaseModel):
    transcript: str


app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")



@app.get("/")
def home():
    return FileResponse("frontend/index.html")



@app.get("/students")
def get_students(
        page: int  = Query(1, ge=1),
        limit: int = Query(10, ge=10, le=100),
        sort_by: str = "student_id",
        sort_order: str = "asc"
):

    # We used allowed_columns list here because column names and sorting directions
    # cannot be safely passed using normal %s SQL placeholders.
    # We only insert values that we've explicitly approved. Never directly insert arbitrary user input into SQL.
    allowed_columns = {
        "student_id",
        "roll_number",
        "name",
        "age",
        "marks"
    }

    if sort_by not in allowed_columns:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting column"
        )

    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting order"
        )

    return get_students_from_database(
            page, limit, sort_by, sort_order.upper()
        )






@app.post("/students", status_code=201)
def create_student(student: StudentCreate):

    try:
         new_student_id = add_student_to_database(student)

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This roll number already exists."
        )

    return {
        "message": "Student added successfully",
        "new_student_id": new_student_id,
        "roll_number": student.roll_number
    }




@app.put("/students/{student_id}")
def update_student(student_id: int, student: StudentCreate):

    try:
        updated = update_student_in_database(student_id, student)

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This roll number already exists."
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "message": "Student updated successfully"
    }




@app.delete("/students/{student_id}")
def delete_student(student_id: int):

    deleted = delete_student_from_database(student_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "message": "Student deleted successfully"
    }


@app.get("/students/search")
def search_students(keyword: str):
    records = search_student_from_database(keyword)
    return records


# POST isn't limited to creating database records. 
# We're sending the transcript in the request body, so POST is a reasonable choice.
# Important: POST does not automatically mean inserting data into MySQL. Our endpoint only reads records.
# We could also use GET with a query parameter:
# But POST keeps the voice transcript out of the URL, which is preferable here.
@app.post("/voice-command")
def process_voice_command(request: VoiceCommandRequest):

    try:
        command = gemini(request.transcript)
    except Exception as error:
        print("Gemini API Error:", error)

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily busy. Please try again."
        )

    if not command["valid"]:
        return {
            "valid": False,
            "message": "Unclear command. Please try again."
        }

    action = command["action"]
    value = command["value"]

    if action in ["search_by_name", "search_by_roll_number"]:
        records = search_student_from_database(value)
        return {
            "valid": True,
            "records": records
        }

    return {
        "valid": False,
        "message": "Unclear command. Please try again."
    }

@app.get("/dashboard/stats")
def dashboard_stats():
    stats = get_dashboard_stats()
    return stats

@app.get("/dashboard/course-distribution")
def course_distribution():
    return get_course_distribution()




@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pending_student = None
    pending_deletion = None
    pending_update = None

    try:
        async with client.aio.live.connect(
                model=MODEL,
                config=LIVE_CONFIG
        ) as session:

            print("Gemini Live Connected")
            await websocket.send_text("connected")

            async def receive_from_gemini():
                nonlocal pending_student, pending_deletion, pending_update
                try:
                    while True:
                        async for response in session.receive():
                            content = response.server_content

                            if response.tool_call:
                                print("Gemini requested a tool:", response.tool_call, flush=True)

                                function_responses = []

                                try:
                                    for fc in response.tool_call.function_calls:
                                        print("Function name:", fc.name, flush=True)
                                        print("Function arguments:", fc.args, flush=True)

                                        if fc.name == "search_student":
                                            result = search_student_from_database(**fc.args)

                                        elif fc.name == "get_student_statistics":
                                            result = get_dashboard_stats()

                                        elif fc.name == "get_course_statistics":
                                            result = get_course_distribution()

                                        elif fc.name == "add_student":
                                            pending_student = StudentCreate(**fc.args)
                                            result = {
                                                "status": "awaiting confirmation",
                                                "student": {
                                                    "roll_number": pending_student.roll_number,
                                                    "name": pending_student.name,
                                                    "age": pending_student.age,
                                                    "course": pending_student.course,
                                                    "marks": pending_student.marks
                                                },
                                                "message": "Student details collected. Read the details to the user and ask for confirmation before registering."
                                            }

                                        elif fc.name == "confirm_student_registration":
                                            if pending_student is None:
                                                result = {
                                                    "status": "error",
                                                    "message": "There is no pending student registration."
                                                }
                                            elif fc.args["confirmed"]:
                                                try:
                                                    new_student_id = add_student_to_database(pending_student)
                                                    result = {
                                                        "status": "success",
                                                        "message": "Student registered successfully.",
                                                        "new_student_id": new_student_id,
                                                        "roll_number": pending_student.roll_number
                                                    }
                                                except IntegrityError:
                                                    result = {
                                                        "status": "error",
                                                        "message": "This roll number already exists. Registration was not completed."
                                                    }
                                                pending_student = None
                                            else:
                                                pending_student = None
                                                result = {
                                                    "status": "cancelled",
                                                    "message": "Student registration cancelled."
                                                }

                                        elif fc.name == "prepare_student_deletion":
                                            records = search_student_from_database(fc.args["keyword"])

                                            if len(records) == 0:
                                                result = {
                                                    "status": "not_found",
                                                    "message": "No student found with those details."
                                                }
                                            elif len(records) > 1:
                                                result = {
                                                    "status": "multiple_matches",
                                                    "students": records,
                                                    "message": "Multiple students found. Ask the user to identify the correct student using their roll number."
                                                }
                                            else:
                                                # fetchall() returns list of dictionaries contain students information.
                                                # So we are using records[0] to access the dictionary inside the list even if the one student record found.
                                                pending_deletion = records[0]
                                                result = {
                                                    "status": "awaiting_confirmation",
                                                    "student": pending_deletion,
                                                    "message": "Read the student details to the user and ask for explicit confirmation before deleting."
                                                }

                                        elif fc.name == "confirm_student_deletion":
                                            if pending_deletion is None:
                                                result = {
                                                    "status": "error",
                                                    "message": "There is no pending student deletion."
                                                }
                                            elif fc.args["confirmed"]:
                                                student_id = pending_deletion["student_id"]
                                                deleted_student = delete_student_from_database(student_id)

                                                if deleted_student:
                                                    result = {
                                                        "status": "success",
                                                        "message": "Student deleted successfully.",
                                                        "student_id": student_id
                                                    }
                                                else:
                                                    # If the student is deleted through another application this might return false.
                                                    # We have to make sure the student exist before saying Yes to deletion.
                                                    # If the student not exists just before the deletion even after found the record,
                                                    # Then it would return false
                                                    result = {
                                                        "status": "error",
                                                        "message": "Student could not be found in the database."
                                                    }
                                                pending_deletion = None

                                            else:
                                                pending_deletion = None
                                                result = {
                                                    "status": "cancelled",
                                                    "message": "Student deletion cancelled. No records were deleted."
                                                }

                                        elif fc.name == "prepare_student_update":
                                            try:
                                                student_id = fc.args["student_id"]
                                                # StudentUpdate(**fc.args["updates"]) passes Gemini's dictionary into the Pydantic model for validation.
                                                # Pydantic validates the marks and creates a model instance.
                                                # .model_dump(exclude_unset=True) converts that model back into a dictionary containing only the fields Gemini supplied.
                                                updates = StudentUpdate(**fc.args["updates"]).model_dump(
                                                    exclude_unset=True)

                                                if not updates:
                                                    raise ValueError("No fields provided for update.")

                                                pending_update = {
                                                    "student_id": student_id,
                                                    "updates": updates
                                                }

                                                result = {
                                                    "status": "awaiting_confirmation",
                                                    "student_id": student_id,
                                                    "updates": updates,
                                                    "message": (
                                                        "Read the requested changes to the user "
                                                        "and ask for explicit confirmation before updating."
                                                    )
                                                }
                                            except ValueError as error:
                                                result = {
                                                    "status": "validation_error",
                                                    "message": str(error)
                                                }

                                        elif fc.name == "confirm_student_update":
                                            if pending_update is None:
                                                result = {
                                                    "status": "error",
                                                    "message": "There is no pending student update."
                                                }
                                            elif fc.args["confirmed"]:
                                                student_id = pending_update["student_id"]
                                                updates = pending_update["updates"]

                                                try:
                                                    updated = update_student_fields_in_database(student_id, updates)

                                                    if updated:
                                                        result = {
                                                            "status": "success",
                                                            "message": "Student details updated successfully.",
                                                            "student_id": student_id,
                                                            "updates": updates
                                                        }
                                                    # If the student is deleted through another application this might return false.
                                                    # We have to make sure the student exist before saying Yes to deletion.
                                                    # If the student not exists just before the deletion even after found the record,
                                                    # Then it would return false
                                                    else:
                                                        result = {
                                                            "status": "not_found",
                                                            "message": "Student could not be found"
                                                        }
                                                except IntegrityError:
                                                    result = {
                                                        "status": "error",
                                                        "message": "That roll number already belongs to another student. Please provide a different one."
                                                    }
                                                except ValueError as error:
                                                    result = {
                                                        "status": "error",
                                                        "message": str(error)
                                                    }
                                                pending_update = None

                                            else:
                                                pending_update = None
                                                result = {
                                                    "status": "cancelled",
                                                    "message": "Student update cancelled. No changes were made."
                                                }


                                        else:
                                            continue

                                        result = json.loads(json.dumps(result, default=float))
                                        print("Database search result:", result)

                                        function_responses.append(
                                            types.FunctionResponse(
                                                name=fc.name,
                                                id=fc.id,
                                                response={"result": result}
                                            )
                                        )
                                    await session.send_tool_response(
                                        function_responses=function_responses
                                    )
                                except Exception as error:
                                    print("Tool execution error:", repr(error), flush=True)
                                    result = {
                                        "status": "error",
                                        "message": {
                                            "The requested operation could not be completed. "
                                            "Please apologize to the user and ask them to try again."
                                        }
                                    }
                                print("Tool response sent back to Gemini")

                            if content is None:
                                # Lifecycle/control messages (e.g. session_resumption_update)
                                continue

                            if content.interrupted:
                                print("Gemini response interrupted by user", flush=True)
                                await websocket.send_text("interrupted")
                                continue

                            if content.input_transcription and content.input_transcription.text:
                                print("User speech:", content.input_transcription.text, flush=True)

                            if content.output_transcription and content.output_transcription.text:
                                print("Gemini speech:", content.output_transcription.text, flush=True)





                            if content.model_turn:
                                for part in content.model_turn.parts:
                                    if part.inline_data and part.inline_data.data:
                                        audio_data = part.inline_data.data
                                        await websocket.send_bytes(audio_data)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    print("Gemini receive error:", repr(error), flush=True)
                    # Letting frontend notify that error occurred, so the application won't crash calmly.
                    try:
                        await websocket.send_text("error")
                    except Exception:
                        pass
                    await websocket.close()

            receiver_task = asyncio.create_task(receive_from_gemini())

            try:
                packet_count = 0
                while True:
                    data = await websocket.receive_bytes()
                    packet_count += 1
                    if packet_count == 1 or packet_count % 50 == 0:
                        print(f"Audio packets received from browser: {packet_count} ({len(data)} bytes)", flush=True)
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=data,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )
            finally:
                receiver_task.cancel()

                # This ensures the background receiver finishes cancelling before the Gemini session closes.
                try:
                    await receiver_task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        print("Client Disconnected")
    except Exception as error:
        print("WebSocket session error:", repr(error), flush=True)
        # Letting frontend notify that error occurred, so the application won't crash calmly.
        try:
            await websocket.send_text("error")
        except Exception:
            pass


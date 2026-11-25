import asyncio

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.genai import types
from mysql.connector.errors import IntegrityError
from pydantic import BaseModel, Field

from gemini_live import client, MODEL, LIVE_CONFIG
from student_repository import get_students_from_database, add_student_to_database, update_student_in_database, \
    delete_student_from_database, search_student_from_database, get_dashboard_stats, get_course_distribution
from voice_ai import gemini


class StudentCreate(BaseModel):
    roll_number: str = Field(min_length=3, max_length=30)
    name: str = Field(min_length=3, max_length=20)
    age: int = Field(gt=0)
    course: str = Field(min_length=3, max_length=20)
    marks: float = Field(ge=0, le=100)


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

    try:
        async with client.aio.live.connect(
                model=MODEL,
                config=LIVE_CONFIG
        ) as session:

            print("Gemini Live Connected")
            await websocket.send_text("connected")

            async def receive_from_gemini():
                while True:
                    async for response in session.receive():
                        print("Gemini response received:", response, flush=True)
                        content = response.server_content
                        print("Content:", content)
                        if content is not None:
                            print("Server content received:", content, flush=True)

                            if content.input_transcription:
                                print("Recognized speech:", content.input_transcription.text, flush=True)

                            if content.model_turn:
                                print("Gemini model turn received", flush=True)
                        if content is None:
                            continue
                        if content:
                            if content.model_turn:
                                for part in content.model_turn.parts:
                                    if part.inline_data:
                                        audio_data = part.inline_data.data
                                        print("Sending audio to browser:", len(audio_data), flush=True)
                                        await websocket.send_bytes(audio_data)

            receiver_task = asyncio.create_task(receive_from_gemini())

            try:
                while True:
                    data = await websocket.receive_bytes()
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


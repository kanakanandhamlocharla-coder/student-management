# Student Management System

A web-based Student Management System built using Python, FastAPI, MySQL, HTML, CSS, and JavaScript. It helps manage student records through a simple and interactive interface.

## Features

- **Dashboard:** Displays student statistics and course distribution.
- **Student Registration:** Add new student records.
- **View Students:** Display all registered students.
- **Update Student Details:** Update complete or selected student information.
- **Delete Students:** Remove student records.
- **Search and Sorting:** Find and organize student records.
- **Pagination:** Navigate through student records efficiently.
- **NOVA AI Assistant:** Integrated AI voice assistant powered by Gemini Live API.
- **Settings:** Enable or disable the AI assistant.

## Technologies Used

- Python
- FastAPI
- MySQL
- HTML
- CSS
- JavaScript
- Gemini API
- Chart.js


## Project Structure

```text
StudentManagement/
│
├── frontend/
│   ├── index.html
│   ├── audio_processor.js
│   ├── script.js
│   └── style.css
│
├── app.py
├── database.py
├── student_repository.py
├── gemini_live.py
├── requirements.txt
│
├── .env
├── .gitignore
└── README.md
```


## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd StudentManagement
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages for the project.

### 4. Configure Environment Variables

Create a `.env` file in the project root and add your required configuration, including your Gemini API key and database credentials.

### 5. Run the Application

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

### 6. Open the Application

Access the application through your browser using the local address configured by the project.

FastAPI API documentation:

```text
http://127.0.0.1:8000/docs
```

## Author

Developed as a learning project to practice backend development, database integration, frontend development, and AI integration.
// Get the registration form from the HTML
const studentForm = document.getElementById("studentForm");

// If user clicked "Edit" (student data) in the table.
let editingStudentId = null;

// For pagination below the table
let currentPage = 1
let totalPages = 1
const pageLimit = 10

let isAgentRunning = false
let isAgentMuted = false

let socket;
let micStream;
let audioContext;
let playbackContext;
let nextPlaybackTime = 0;
let activeAudioSources = [];
let microphoneSource;
let audioWorkletNode;
let silentGainNode;
let audioPacketCount = 0;


const submitButton = studentForm.querySelector("button[type='submit']")
const cancelEditButton = document.getElementById("cancelEditButton")
//Live Agent Controls
const agentStartStopButton = document.getElementById("agentStartStopButton")
const agentMuteButton = document.getElementById("agentMuteButton")
const agentStatus = document.getElementById("agentStatus")
const agentActivity = document.getElementById("agentActivity")

//Listen for form Submission
studentForm.addEventListener("submit", async function(event) {

    //Prevent the browser's default form submission
    event.preventDefault();

    const studentData = {
        roll_number: document.getElementById("roll_number").value,
        name: document.getElementById("name").value,
        age: Number(document.getElementById("age").value),
        course: document.getElementById("course").value,
        marks: Number(document.getElementById("marks").value)
    };

    // Check whether fields contain only spaces
    if (
        studentData.roll_number.trim() === "" ||
        studentData.name.trim() === "" ||
        studentData.course.trim() === ""
    ) {
        alert("Please enter valid information in all fields");
        return;
    }

    // Check age
    if (
        studentData.age <= 0 || !Number.isInteger(studentData.age)
    ) {
        alert("Please enter a valid age.");
        return;
    }

    //Check marks
    if (
        !Number.isFinite(studentData.marks) ||
        studentData.marks < 0 ||
        studentData.marks > 100
    ) {
        alert("Marks must be between 0 and 100.");
        return;
    }

    // Helps to change the url and method for fetch() because the same form is being used for both POST and PUT.
    let url = "/students";
    let method = "POST"


    // If "Edit" option picked by user, we change the url and method so the form changes to PUT.
    if (editingStudentId !== null) {
        url = `/students/${editingStudentId}`;
        method = "PUT"
    }

    try {

        const response = await fetch(url, {
        method: method,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(studentData)
    });

    // Read the response from FastAPI
    const result = await response.json();

    if(response.ok) {
        if (editingStudentId === null) {
            alert("Student registered successfully");
        }
        else {
            alert("Student updated successfully");
        }

        // Reset editing student ID so again the form sets to default method "POST" *************
        editingStudentId = null;

        studentForm.reset();
        submitButton.textContent = "Add Student";
        cancelEditButton.hidden = true;
        await load_students();
    } else {
        alert(result.detail || "Something went wrong.");
    }

    }
    catch (error) {
        console.error("Error:", error)
        alert("Unable to connect to the server. Please try again.");
    }
});



// Displaying student records in the HTML table (Runs when user clicked "search button" or "show all" button)
function displayStudents(students) {
    const tableBody = document.getElementById("studentTableBody");

    tableBody.innerHTML = "";

    // Shows No students found if search result is empty or students records in database are empty
    if(students.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 7;
        cell.textContent = "No students found";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    students.forEach(function(student) {
        const row = document.createElement("tr");

        const values = [
            student.student_id,
            student.roll_number,
            student.name,
            student.age,
            student.course,
            student.marks,

        ];
        values.forEach(function (value){
           const cell =  document.createElement("td");
           cell.textContent = value ?? "";
           row.appendChild(cell);
        });

       // Creating an action cell
        const actionCell = document.createElement("td")
        const editButton = document.createElement("button")
        editButton.textContent = "Edit";
        editButton.addEventListener("click", function () {
            editStudent(student);
        });
        const deleteButton = document.createElement("button")
        deleteButton.textContent = "Delete"
        deleteButton.addEventListener("click", function (){
            deleteStudent(student.student_id)
        })
        actionCell.appendChild(editButton);
        actionCell.appendChild(deleteButton);
        row.appendChild(actionCell);
        tableBody.appendChild(row);
    });
}



// When a user clicked the Edit button, the form gets filled with the existing student details by scrolling over to the top smoothly.
function editStudent(student) {

    editingStudentId = student.student_id

    // Form gets filled with the student data when user clicked Edit
    document.getElementById("roll_number").value = student.roll_number
    document.getElementById("name").value = student.name
    document.getElementById("age").value = student.age
    document.getElementById("course").value = student.course
    document.getElementById("marks").value = student.marks

    submitButton.textContent = "Update Student";
    cancelEditButton.hidden = false;

    // Open the student registration section
    contentSections.forEach(section => {
        section.classList.remove("active-section")
    })
    document.getElementById("registration").classList.add("active-section")

    // Update sidebar active appearance
    navItems.forEach(item => {
        item.classList.remove("active")
        if (item.dataset.section === "registration") {
            item.classList.add("active")
        }
    })


}


// Function to cancel editing the form
function cancelEdit() {
    editingStudentId = null;
    studentForm.reset();
    submitButton.textContent = "Add Student";
    cancelEditButton.hidden = true
}


// Function to delete student
async function deleteStudent(studentID) {

    const confirmed = confirm("Are you sure you want to delete this student?");

    if(!confirmed) {
        return;
    }

    try {

        const response = await fetch(`/students/${studentID}`, {method: "DELETE"});
        const result = await response.json()
        if (response.ok) {
            alert("Student deleted successfully")
            await load_students()
        } else {
            alert(result.detail || "Unable to delete the student.")
        }
    }
    catch (error) {
        console.error("Delete Error:", error);
        alert("Unable to connect to the server");
    }
}




// Retrieve all students from FastAPI and displays students records in the HTML Table
async function load_students(page = 1) {

   try {

       const sortBy = document.getElementById("sortBy").value;
       const sortOrder = document.getElementById("sortOrder").value;

       const response = await fetch(
           `/students?page=${page}&limit=${pageLimit}&sort_by=${sortBy}&sort_order=${sortOrder}`
       );

       if (!response.ok) {
           throw new Error("Failed to retrieve student records.")
       }

       const result = await response.json();

       currentPage = result.page;
       totalPages = result.total_pages;
       displayStudents(result.students);
       document.getElementById("previousButton").disabled = currentPage === 1;
       document.getElementById("pageInfo").textContent = `Page ${currentPage} of ${totalPages}`;
       document.getElementById("nextButton").disabled = currentPage >= totalPages;
   }
   catch (error) {
       console.error("Error loading students:", error)
       alert("Unable to fetch student records")
   }

}

// Function for search students using name or roll number
async function searchStudents() {
    const keyword = document.getElementById("searchInput").value.trim();

    if(keyword === "") {
        alert("Please Enter student name or roll number");
        return;
    }
    const response = await fetch(
        `/students/search?keyword=${encodeURIComponent(keyword)}`
    );
    const students = await response.json();
    displayStudents(students);
}

// this function helps to show or hide the pagination buttons and text when voice search is disabled or enabled
function togglePagination(show) {
    document.getElementById("previousButton").style.display = show ? "inline-block": "none";
    document.getElementById("nextButton").style.display = show ? "inline-block": "none";
    document.getElementById("pageInfo").style.display = show ? "inline-block": "none";
}


// Search students when "Search" button clicked
document.getElementById("searchButton").addEventListener("click", () => {togglePagination(false); searchStudents()});

// Student records appear when "Show All" Button clicked
document.getElementById("showAllButton").addEventListener("click", () => {
    document.getElementById("searchInput").value = ""; togglePagination(true);
    currentPage = 1; load_students(1)
});

// Edit gets canceled
cancelEditButton.addEventListener("click", cancelEdit);

// New students records load into the table when "Previous" or "Next" Button clicked using load_students()
// Here the function gets returned when isVoiceSearch is true, Even though they are hidden (for safety)
document.getElementById("previousButton").addEventListener("click", function () {
     load_students(currentPage - 1) });
document.getElementById("nextButton").addEventListener("click", function () {
    load_students(currentPage + 1)});

// Applying sort when clicked, Also We have given page number for that parameter because its usual parameter is 1.
document.getElementById("sortButton").addEventListener("click", function () {load_students(1)})

// Loads the data instantly after the webpage opens
load_students();






// SideBar Navigation
const navItems = document.querySelectorAll(".nav-item");
const contentSections = document.querySelectorAll(".content-section")

// Adding click event to each navigation item
navItems.forEach(item => {
    item.addEventListener("click", (event) => {
        event.preventDefault()

        // Getting the selected section name
        const sectionName = item.dataset.section;

        // Finding the corresponding section
        const selectedSection = document.getElementById(sectionName)

        // Hide all sections
        contentSections.forEach(section => {
            section.classList.remove("active-section")
        })

        // Remove active appearance from all navigation items
        navItems.forEach(item => {
            item.classList.remove("active")
        })

        // Display selected section
        selectedSection.classList.add("active-section")
        // Letting the dashboard fetches the data everytime when dashboard nav item clicked
        if (sectionName === "dashboard") {
            loadDashboardStats()
            loadRecentStudents()
            loadCourseDistribution()
        }

        // Highlight selected navigation item
        item.classList.add("active")
    })
})


// Load Dashboard Statistics

async function loadDashboardStats() {

    try {
        const response = await fetch("/dashboard/stats")
        const stats = await response.json()

        document.getElementById("totalStudents").textContent = stats.total_students
        document.getElementById("totalCourses").textContent = stats.total_courses
        document.getElementById("averageMarks").textContent = stats.average_marks ?? 0
        document.getElementById("highestMarks").textContent = stats.highest_marks ?? 0

    } catch (error) {
        console.error("Dashboard loading error:", error)
    }
}
loadDashboardStats()
loadRecentStudents()
loadCourseDistribution()

// Load Recent Students in Dashboard Section
async function loadRecentStudents() {

    try {
        // Requesting limit=10 because the FastAPI endpoint function's "limit" was set to 10. so we request 10 and slice to 5
        const response = await fetch("/students?page=1&limit=10&sort_by=student_id&sort_order=desc");
        const data = await response.json()

        const tableBody = document.getElementById("recentStudentsBody")
        tableBody.innerHTML = "";

        // slice(0, 5) retrieves first 5 records.
       data.students.slice(0, 5).forEach(student => {
            const row = document.createElement("tr")

            row.innerHTML = `
                <td>${student.roll_number}</td>
                <td>${student.name}</td>
                <td>${student.course}</td>
                <td>${student.marks}</td>
            `;
            tableBody.appendChild(row)
        });
    } catch (error) {
        console.error("Recent students loading error:", error)
    }
}




// Load Course Distribution Chart
let courseChart = null

async function loadCourseDistribution(){

    try {
        const response = await fetch("/dashboard/course-distribution")
        const courses = await response.json()

        const labels = courses.map(course => course.course)
        const values = courses.map(course => course.student_count)
        const ctx = document.getElementById("courseChart")

        if (courseChart) {
            courseChart.destroy()
        }
        courseChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,

                    backgroundColor: [
                        "#4e79a7",
                        "#f28e2b",
                        "#59a14f",
                        "#e15759",
                        "#af7aa1"
                    ],

                    borderColor: "#ffffff",
                    borderWidth: 3,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {

                                const total = context.dataset.data.reduce(
                                    (sum, value) => sum + value, 0
                                );

                                const value = context.raw;

                                const percentage = ((value / total) * 100).toFixed(1);

                                return `${context.label}: ${value} students (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        })
    }
    catch (error) {
        console.error("Course chart loading error:", error)
    }
}






function stopAudioPlayback() {
    for (const source of activeAudioSources) {
        try {
            source.stop();
        } catch (e) {
            // Ignore if source already finished
        }
        source.disconnect();
    }
    activeAudioSources = [];
    nextPlaybackTime = playbackContext ? playbackContext.currentTime : 0;
}

function playPcmAudio(arrayBuffer) {
    if (!playbackContext) {
        playbackContext = new AudioContext({ sampleRate: 24000 });
        nextPlaybackTime = playbackContext.currentTime;
    }
    if (playbackContext.state === "suspended") {
        playbackContext.resume();
    }

    const int16 = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
    }

    const audioBuffer = playbackContext.createBuffer(1, float32.length, 24000);
    audioBuffer.getChannelData(0).set(float32);

    const source = playbackContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(playbackContext.destination);

    source.onended = () => {
        activeAudioSources = activeAudioSources.filter(s => s !== source);
    };
    activeAudioSources.push(source);

    const startTime = Math.max(playbackContext.currentTime, nextPlaybackTime);
    source.start(startTime);
    nextPlaybackTime = startTime + audioBuffer.duration;
}

agentStartStopButton.addEventListener("click", async () => {

    if (!isAgentRunning) {

        try {
            agentStatus.textContent = "Connecting...";
            agentActivity.textContent = "Connecting to NOVA...";
            audioPacketCount = 0;

            const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
            const wsHost = window.location.host || "127.0.0.1:8000";
            socket = new WebSocket(`${wsProtocol}://${wsHost}/ws`);

            socket.onopen = () => {
                console.log("WebSocket Connected");
            };

            socket.onmessage = async (event) => {
                if (typeof event.data === "string") {
                    console.log("Message from FastAPI:", event.data);
                    if (event.data === "connected") {
                        agentStatus.textContent = "Listening";
                        agentActivity.textContent = "Connected! Speak into your microphone.";
                    } else if (event.data === "interrupted") {
                        stopAudioPlayback();
                        agentStatus.textContent = "Listening";
                        agentActivity.textContent = "Interrupted — listening...";
                    }
                    else if (event.data === "error") {
                        stopAudioPlayback()
                        agentStatus.textContent = "Error"
                        agentActivity.textContent = "Sorry, something went wrong. Please try again."
                    }
                    return;
                }

                const audioData = await event.data.arrayBuffer();
                console.log("Gemini audio received:", audioData.byteLength);
                agentActivity.textContent = "NOVA is speaking...";
                playPcmAudio(audioData);
            };

            socket.onerror = (error) => {
                console.error("WebSocket Error:", error);
                agentStatus.textContent = "Error";
                agentActivity.textContent = "WebSocket connection error.";
            };

            socket.onclose = (event) => {
                console.log("WebSocket closed:", event.code, event.reason);
                if (isAgentRunning) {
                    agentStatus.textContent = "Disconnected";
                }
            };

            micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioContext = new AudioContext({ sampleRate: 16000 });
            await audioContext.resume();
            console.log("Audio Sample Rate:", audioContext.sampleRate);

            await audioContext.audioWorklet.addModule("/static/audio_processor.js");
            microphoneSource = audioContext.createMediaStreamSource(micStream);
            audioWorkletNode = new AudioWorkletNode(audioContext, "audio-processor");

            // Connect through a zero-gain node to destination so the browser always pulls process()
            silentGainNode = audioContext.createGain();
            silentGainNode.gain.value = 0;

            audioWorkletNode.port.onmessage = (event) => {
                const pcmSamples = event.data;
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(pcmSamples.buffer);
                    audioPacketCount += 1;
                    if (audioPacketCount === 1 || audioPacketCount % 50 === 0) {
                        console.log("Sent audio packets:", audioPacketCount, pcmSamples.byteLength, "bytes");
                    }
                }
            };

            microphoneSource.connect(audioWorkletNode);
            audioWorkletNode.connect(silentGainNode);
            silentGainNode.connect(audioContext.destination);

            isAgentRunning = true;
            agentStartStopButton.textContent = "Stop";
            agentMuteButton.disabled = false;
            agentStartStopButton.classList.add("active");
        }
        catch (error) {
            console.error("Microphone error:", error);
            agentStatus.textContent = "Error";
            agentActivity.textContent = `Failed to start: ${error.message}`;
        }
    }
    else {

        if (micStream) {
            micStream.getTracks().forEach(track => track.stop());
        }
        if (microphoneSource) {
            microphoneSource.disconnect();
        }
        if (audioWorkletNode) {
            audioWorkletNode.disconnect();
        }
        if (silentGainNode) {
            silentGainNode.disconnect();
        }
        if (audioContext) {
            await audioContext.close();
            audioContext = null;
        }
        if (playbackContext) {
            stopAudioPlayback();
            await playbackContext.close();
            playbackContext = null;
            nextPlaybackTime = 0;
        }
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }

        isAgentRunning = false;
        isAgentMuted = false;

        agentStatus.textContent = "Ready";
        agentActivity.textContent = "Session stopped.";
        agentStartStopButton.textContent = "Start";
        agentMuteButton.textContent = "Mute";
        agentMuteButton.disabled = true;
        agentStartStopButton.classList.remove("active");
        agentMuteButton.classList.remove("muted");
    }
})


agentMuteButton.addEventListener("click", () => {
    isAgentMuted = !isAgentMuted

    micStream.getTracks().forEach(track => {
        track.enabled = !isAgentMuted
    })

    agentMuteButton.textContent = isAgentMuted ? "Unmute" : "Mute"
    agentMuteButton.classList.toggle("muted", isAgentMuted);
})

const aiToggle = document.getElementById("aiToggle")
aiToggle.addEventListener("click", () => {

    const isEnabled = aiToggle.classList.toggle("on")

    aiToggle.setAttribute("aria-pressed", isEnabled)

    // Enable or disable the AI Agent Start button
    if (!isEnabled && isAgentRunning) {
        agentStartStopButton.click()
    }
    agentStartStopButton.disabled = !isEnabled
})






















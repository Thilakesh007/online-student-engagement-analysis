import flask
import os
from flask import Flask, jsonify, render_template_string, send_file
import threading, time, math, csv
import numpy as np
from datetime import datetime

print("🔥 FULL AI ENGAGEMENT SYSTEM RUNNING 🔥")

app = Flask(__name__)

app.secret_key = "engagement_secret_key"

# 🔐 REQUIRED FOR ngrok / HTTPS sessions
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)


# ================= GLOBAL VARIABLES =================
# ================= GLOBAL VARIABLES =================
# ================= LOGIN USERS =================
USERS = {
    "student1": {"password": "student123", "role": "student"},
    "faculty1": {"password": "faculty123", "role": "faculty"}
}


last_metric_time = None


presence_time = 0.0
engagement_time = 0.0
attention_time = 0.0

engagement_score = 0
attention_score = 0

status = "Idle"
emotion = "Neutral 😐"
attendance = "Absent ❌"
movement_state = "Idle 🟡"
session_start_time = None
emotion_log = []

# Current student name (dynamic)
current_student = ""

# ================= STUDENT RUNTIME STORE =================
students = {}

# CSV file path
CSV_FILE = "session_report.csv"

engagement_level = "Not Evaluated ⏳"

running = False
ATTENDANCE_THRESHOLD = 20

performance_grade = "-"

# 🔥 GRAPH HISTORY (ADDED)
engagement_history = []
attention_history = []



# ================= ENGAGEMENT CLASSIFICATION =================
def classify_engagement(score):
    if score >= 80:
        return "High Engagement 🔥"
    elif score >= 45:
        return "Moderate Engagement 🙂"
    else:
        return "Low Engagement 😴"

# ================= SESSION SUMMARY REPORT =================
def generate_session_report():
    filename = f"session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    avg_engagement = int(sum(engagement_history)/len(engagement_history)) if engagement_history else 0
    avg_attention = int(sum(attention_history)/len(attention_history)) if attention_history else 0

    dominant_emotion = max(set(emotion_log), key=emotion_log.count) if emotion_log else "Unknown"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Presence Time (sec)", int(presence_time)])
        writer.writerow(["Average Engagement (%)", avg_engagement])
        writer.writerow(["Average Attention (%)", avg_attention])
        writer.writerow(["Final Attendance", attendance])
        writer.writerow(["Dominant Emotion", dominant_emotion])

    return filename
    

# ================= UI =================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>

<style>

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulseSoft {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
}

.login-card{
  max-width:380px;
  margin:auto;
  margin-top:12vh;
  padding:30px;
  background:white;
  border-radius:18px;
  box-shadow:0 20px 40px rgba(0,0,0,0.1);
  animation: fadeInUp 0.8s ease;
}


:root{
  --bg-main:#f8fafc;
  --bg-card:#ffffff;
  --border:#e5e7eb;
  --primary:#2563eb;
  --text-main:#111827;
  --text-muted:#6b7280;
}

body.dark{
  --bg-main:#0b1120;
  --bg-card:#111827;
  --border:#1f2937;
  --primary:#3b82f6;
  --text-main:#e5e7eb;
  --text-muted:#9ca3af;
}

body{
  background:var(--bg-main);
  font-family:'Segoe UI',system-ui;
  display:flex;
  justify-content:center;
  align-items:center;
  height:100vh;
  transition:background 0.3s ease;
}

.card{
  background:var(--bg-card);
  width:380px;
  padding:32px;
  border-radius:16px;
  border:1px solid var(--border);
  box-shadow:0 12px 32px rgba(0,0,0,0.08);
  animation:slideFade 0.6s ease-out;
}

@keyframes slideFade{
  from{opacity:0; transform:translateY(20px)}
  to{opacity:1; transform:translateY(0)}
}

.toggle{
  position:absolute;
  top:20px;
  right:20px;
  cursor:pointer;
  font-size:18px;
}

h2{margin-bottom:6px}
.subtitle{
  color:var(--text-muted);
  margin-bottom:20px;
  font-size:14px;
}

input, select{
  width:100%;
  padding:12px;
  margin:10px 0;
  border-radius:10px;
  border:1px solid var(--border);
  font-size:14px;
  background:transparent;
  color:var(--text-main);
}

input:focus, select:focus{
  outline:none;
  border-color:var(--primary);
  box-shadow:0 0 0 3px rgba(37,99,235,0.15);
}

button{
  width:100%;
  padding:12px;
  margin-top:15px;
  border:none;
  border-radius:10px;
  background:var(--primary);
  color:white;
  font-size:16px;
  font-weight:600;
  cursor:pointer;
  transition:all 0.2s ease;
}

button.loading{
  background:#94a3b8;
  pointer-events:none;
}

.demo{
  background:rgba(148,163,184,0.15);
  border:1px dashed var(--border);
  border-radius:12px;
  padding:12px;
  margin-top:18px;
  font-size:13px;
}

.error{
  color:#dc2626;
  font-size:14px;
  margin-top:10px;
}

.loader{
  display:none;
  text-align:center;
  margin-top:15px;
  font-size:14px;
}
</style>

</head>
<body>

<div class="toggle" onclick="toggleTheme()">🌙</div>

<div class="card">
  <h2>Welcome Back 👋</h2>
  <div class="subtitle">Login to Student Engagement System</div>

  <form method="POST" onsubmit="showLoader()">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>

    <select name="role">
      <option value="student">Student</option>
      <option value="faculty">Faculty</option>
    </select>

    <button id="loginBtn">Sign In</button>
  </form>

  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}

  <div class="loader" id="loader">🔄 Signing in...</div>

</div>



<script>
function toggleTheme(){
  document.body.classList.toggle("dark");
  document.querySelector(".toggle").innerText =
    document.body.classList.contains("dark") ? "☀️" : "🌙";
}

function showLoader(){
  document.getElementById("loginBtn").classList.add("loading");
  document.getElementById("loginBtn").innerText="Signing in...";
  document.getElementById("loader").style.display="block";
}
</script>

</body>
</html>
"""


HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Student Engagement Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulseSoft {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
}


:root{
  --bg-main:#f8fafc;
  --bg-card:#ffffff;
  --border:#e5e7eb;

  --primary:#2563eb;
  --success:#16a34a;
  --danger:#dc2626;
  --warning:#f59e0b;

  --text-main:#111827;
  --text-muted:#6b7280;
}

body{
  background:var(--bg-main);
  color:var(--text-main);
  font-family:Arial;
  text-align:center;
}

button:hover{
  transform:translateY(-1px);
  box-shadow:0 6px 18px rgba(37,99,235,0.35);
}


.container{
  max-width:1200px;
  margin:auto;
  padding:20px;
  text-align:center;
}

.card{
  background:var(--bg-card);
  border:1px solid var(--border);
  border-radius:16px;
  padding:16px;
  margin:8px;
  box-shadow:0 10px 25px rgba(0,0,0,0.08);

  animation: fadeInUp 0.6s ease forwards;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover{
  transform: translateY(-4px);
  box-shadow:0 16px 32px rgba(0,0,0,0.12);
}

.live-engagement{
  animation: pulseSoft 1.5s infinite;
}

.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:16px;
  margin-top:20px;
}

button{
  padding:10px 22px;
  border:none;
  border-radius:8px;
  font-size:15px;
  font-weight:600;
  cursor:pointer;
  background:var(--primary);
  color:white;
}
button:hover{
  opacity:0.9;
}


.start{background:var(--success)}
.stop{background:var(--danger)}
.faculty{background:var(--primary)}


input{
  background:white;
  border:1px solid #e5e7eb;
  color:#111827;
  padding:10px;
  border-radius:8px;
}

.card:hover{
  transform:translateY(-2px);
  transition:0.2s;
}


.badge{
  padding:6px 16px;
  border-radius:999px;
  font-weight:600;
  font-size:14px;
  animation: fadeInUp 0.4s ease;
}
.engaged{
  background:#dcfce7;
  color:#166534;
  box-shadow:0 0 0 0 rgba(34,197,94,0.6);
}


.engaged{background:#dcfce7;color:#166534}
.distracted{background:#fee2e2;color:#991b1b}
.neutral{background:#fef9c3;color:#854d0e}


.engaged{background:#16a34a}
.distracted{background:#dc2626}
.neutral{background:#f59e0b;color:black}
</style>

</head>
<body>

<body>
<div class="container">

<!-- STUDENT PROFILE CARD -->
<div class="card" style="max-width:420px;margin:auto;text-align:left">
  <h3>👤 Student Profile</h3>
  <p><b>Name:</b> <span id="sname">John Doe</span></p>
  <p><b>Student ID:</b> <span id="sid">AI2025</span></p>
  <p><b>Status:</b> <span id="sstatus">-</span></p>
  <p><b>Engagement:</b><span id="profileEngagement">0</span>%
  <p><b>Grade:</b> <span id="grade">-</span></p>
</div>

<h1>🎓 Online Student Engagement Analytics</h1>
<p style="color:#9ca3af">AI-based real-time attention monitoring</p>

<input id="student" placeholder="Enter Student Name"
style="padding:8px;border-radius:6px;border:none;margin:5px">

<button onclick="startCamera()">🎥 Enable Camera</button>

<button onclick="window.location.href='/logout'">🚪 Logout</button>

<button class="start" onclick="startSession()">▶ Start</button>

<script>
function startSession(){
  const name = document.getElementById("student").value;
  if(!name){
    alert("Enter student name");
    return;
  }
  fetch("/start?student="+encodeURIComponent(name));
}
</script>

<button class="stop" onclick="stopSession()">⏹ Stop</button>

<script>
function stopSession(){
  const student = document.getElementById("student").value;
  if(!student){
    alert("Enter student name");
    return;
  }

  fetch("/stop?student="+encodeURIComponent(student))
    .then(() => stopCamera());   // 🔥 CAMERA OFF
}
</script>



<button class="faculty" onclick="window.location.href='/faculty'">📊 Faculty Dashboard</button>


<div class="card" style="width:90%;margin:auto">
<h2>👤 Student Live Status</h2>

<h3>🧑 Student: <span id="studentNameDisplay">-</span></h3>

<div style="margin:15px 0;text-align:center">
  
  <video id="video" autoplay muted playsinline
  style="
    width:320px;
    border-radius:12px;
    border:1px solid #e5e7eb;
    transform: scaleX(-1);
  ">
</video>


  <canvas id="canvas" width="320" height="240" style="display:none"></canvas>
</div>


<div class="grid">
  <div class="card"><b>Presence</b><br><span id="p">0</span>s</div>
  <div class="card"><b>Engagement</b><br><span id="e">0</span>%</div>
  <div class="card"><b>Engagement Time</b><br><span id="et">0</span>s</div>
   <div class="card"><b>Engagement Level</b><br><span id="el">-</span></div>
  <div class="card"><b>Attention</b><br><span id="a">0</span>%</div>
  <div class="card"><b>Movement</b><br><span id="mv">-</span></div>
  <div class="card"><b>Attendance</b><br><span id="at">-</span></div>
</div>

<div class="card">
Status:
<span id="statusBadge" class="badge neutral">Idle</span>
</div>



</div>

<canvas id="chart" width="420" height="180"></canvas>

<script>
const ctx=document.getElementById("chart");
const chart=new Chart(ctx,{
type:"line",
data:{
labels:[],
datasets:[
{label:"Engagement %",data:[],borderColor:"#22c55e",borderWidth:2},
{label:"Attention %",data:[],borderColor:"#3b82f6",borderWidth:2}
]},
options:{scales:{y:{min:0,max:100}}}
});
</script>

<script>
setInterval(() => {
  const student = document.getElementById("student").value;
  if (!student) return;

  fetch('/data?student=' + encodeURIComponent(student))
    .then(r => r.json())
    .then(d => {
      if (!d.presence && d.presence !== 0) return;

      document.getElementById("p").innerText = d.presence;
      document.getElementById("et").innerText = d.engagement_time;
      document.getElementById("e").innerText = d.engagement;
      document.getElementById("a").innerText = d.attention;
      document.getElementById("mv").innerText = d.movement;
      document.getElementById("at").innerText = d.attendance;
      document.getElementById("el").innerText = d.engagement_level;
      document.getElementById("studentNameDisplay").innerText = d.student_name;
      document.getElementById("sname").innerText = d.student_name;

      const badge = document.getElementById("statusBadge");
      badge.className =
        d.movement.includes("Engaged") ? "badge engaged" :
        d.movement.includes("Distracted") ? "badge distracted" :
        "badge neutral";

      badge.innerText = d.movement;

      // 🔥 GRAPH UPDATE (ADD THIS)
      const timeLabel = new Date().toLocaleTimeString();

      // limit graph points to last 20
      if (chart.data.labels.length > 20) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
      chart.data.datasets[1].data.shift();
      }
      chart.data.labels.push(timeLabel);
      chart.data.datasets[0].data.push(d.engagement);
      chart.data.datasets[1].data.push(d.attention);
      chart.update();

    });
}, 1000);
</script>





<script src="https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>

<script>
function onResults(results) {

  if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
    sendMetrics(false, 0, 0, 0);
    return;
  }

  const lm = results.multiFaceLandmarks[0];

  function distance(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  const leftEAR =
    (distance(lm[160], lm[144]) + distance(lm[158], lm[153])) /
    (2 * distance(lm[33], lm[133]));

  const rightEAR =
    (distance(lm[385], lm[380]) + distance(lm[387], lm[373])) /
    (2 * distance(lm[362], lm[263]));

  const ear = (leftEAR + rightEAR) / 2;

  const mar = distance(lm[13], lm[14]) / distance(lm[78], lm[308]);

  const noseX = lm[1].x;
  const faceWidth = Math.abs(lm[234].x - lm[454].x);
  const headTurn = Math.abs(
    noseX - (lm[234].x + lm[454].x) / 2
  ) / faceWidth;

  sendMetrics(true, ear, mar, headTurn);
}
</script>

<script>
const faceMesh = new FaceMesh({
  locateFile: (file) =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
});

faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6
});

faceMesh.onResults(onResults);
</script>

<script>
const video = document.getElementById("video");
let mpCamera = null;
let videoStream = null;   

async function startCamera(){
  try{
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false
    });

    video.srcObject = videoStream;
    await video.play();

    mpCamera = new Camera(video, {
      onFrame: async () => {
        await faceMesh.send({ image: video });
      },
      width: 640,
      height: 480
    });

    mpCamera.start();
    console.log("✅ Camera started");
  }catch(err){
    alert("❌ Camera access denied");
    console.error(err);
  }
}

</script>

<script>
function stopCamera(){
  if(videoStream){
    videoStream.getTracks().forEach(track => track.stop());
    video.srcObject = null;
    videoStream = null;
  }

  if(mpCamera){
    mpCamera.stop();
    mpCamera = null;
  }

  console.log("🛑 Camera stopped");
}
</script>


<script>
function sendMetrics(face, ear, mar, headTurn) {
  const student = document.getElementById("student").value;
  if (!student) return;

  fetch("/metrics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      student: student,
      face: face,
      ear: ear,
      mar: mar,
      head: headTurn
    })
  });
}

</script>




</div>
</body>
</html>
"""

FACULTY_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Faculty Dashboard</title>

<style>

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulseSoft {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
}

:root{
  --bg-main:#f8fafc;
  --bg-card:#ffffff;
  --border:#e5e7eb;

  --primary:#2563eb;
  --success:#16a34a;
  --danger:#dc2626;
  --warning:#f59e0b;

  --text-main:#111827;
  --text-muted:#6b7280;
}

body{
  background:var(--bg-main);
  color:var(--text-main);
  font-family:'Segoe UI',system-ui;
}

.container{
  max-width:1200px;
  margin:auto;
  padding:20px;
}



.card{
  background:var(--bg-card);
  border:1px solid var(--border);
  border-radius:16px;
  padding:16px;
  margin:8px;
  box-shadow:0 10px 25px rgba(0,0,0,0.08);

  animation: fadeInUp 0.6s ease forwards;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover{
  transform: translateY(-4px);
  box-shadow:0 16px 32px rgba(0,0,0,0.12);
}


tr:hover{
  background:#f1f5f9;
  cursor:pointer;
}

.card{
  transition:0.2s;
}
.card:hover{
  transform:translateY(-3px);
}


.header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}

button{
  padding:8px 18px;
  border:none;
  border-radius:8px;
  background:var(--primary);
  color:white;
  font-weight:600;
  cursor:pointer;
}

input{
  padding:10px;
  border-radius:8px;
  border:1px solid var(--border);
  width:220px;
}

table{
  width:100%;
  border-collapse:collapse;
  margin-top:15px;
}

th,td{
  padding:12px;
  border-bottom:1px solid var(--border);
  text-align:center;
}

th{
  background:#f1f5f9;
  font-weight:600;
}

tr{
  animation: fadeInUp 0.4s ease;
}


tr:hover{
  background:#f8fafc;
}
</style>

</head>
<body>

<div class="container">

  <div class="header">
    <div>
      <h1> 🎓 Faculty Engagement Dashboard</h1>
      <p style="color:var(--text-muted)">Student performance overview</p>
    </div>
    <button onclick="window.location.href='/logout'">Logout</button>
  </div>

  <!-- TOP STATS -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px">
    <div class="card">
      <b>Total Students</b><br>
      <span style="font-size:26px">{{ records|length }}</span>
    </div>
  </div>

  <!-- SEARCH -->
  <input id="search" placeholder="Search Student..." onkeyup="filterTable()">

  <!-- TABLE -->
  <div class="card">
    <table>
      <tr>
        <th>Student Name</th>
        <th>Date</th>
        <th>Presence (s)</th>
        <th>Engagement (s)</th>
        <th>Engagement %</th>
        <th>Attention %</th>
        <th>Attendance</th>
        <th>Grade</th>
      </tr>

      {% for r in records %}
      <tr>
        <td>{{r[0]}}</td>
        <td>{{r[1]}}</td>
        <td>{{r[2]}}</td>
        <td>{{r[3]}}</td>
        <td>{{r[4]}}</td>
        <td>{{r[5]}}</td>
        <td>{{r[6]}}</td>
        <td style="
          font-weight:600;
          color:
          {% if 'A' in r[7] %}#16a34a
          {% elif 'B' in r[7] %}#2563eb
          {% elif 'C' in r[7] %}#f59e0b
          {% else %}#dc2626
          {% endif %}
        ">
        {{ r[7] }}
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

</div>

<script>
function filterTable(){
  let input=document.getElementById("search").value.toUpperCase();
  let rows=document.querySelectorAll("table tr");
  rows.forEach((r,i)=>{
    if(i===0) return;
    r.style.display = r.innerText.toUpperCase().includes(input) ? "" : "none";
  });
}
</script>

</body>
</html>
"""


# ================= ROUTES =================
from flask import session, redirect, request
@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        role = flask.request.form["role"]

        user = USERS.get(username)

        if user and user["password"] == password and user["role"] == role:
            session["user"] = username
            session["role"] = role

            if role == "faculty":
                return redirect("/faculty")
            else:
                return redirect("/")
        else:
            return render_template_string(LOGIN_HTML, error="Invalid login")

    return render_template_string(LOGIN_HTML)


@app.route("/")
def home():
    if "user" not in session or session.get("role") != "student":
        return redirect("/login")
    return render_template_string(HTML, student_name=current_student)



@app.route("/start")
def start():
    student = request.args.get("student")
    if not student:
        return "Student name missing", 400

    students[student] = {
        "presence": 0,
        "engagement_time": 0,
        "attention_time": 0,
        "engagement_score": 0,
        "attention_score": 0,
        "attendance": "Absent ❌",
        "movement": "Idle 🟡",
        "engagement_level": "Not Evaluated ⏳",
        "last_metric_time": None,
        "running": True
    }

    return "Started"



@app.route("/stop")
def stop():
    student = request.args.get("student")
    if not student or student not in students:
        return "Invalid student", 400

    s = students[student]
    s["running"] = False

    avg_eng = s["engagement_score"]
    avg_att = s["attention_score"]
    final = (avg_eng + avg_att) / 2

    grade = (
        "A 🏆" if final >= 80 else
        "B 🥈" if final >= 60 else
        "C 🥉" if final >= 40 else
        "D ❌"
    )

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow([
                "Student","Date","Presence",
                "Engagement Time","Engagement %",
                "Attention %","Attendance","Grade"
            ])
        w.writerow([
            student,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            s["presence"],
            s["engagement_time"],
            s["engagement_score"],
            s["attention_score"],
            s["attendance"],
            grade
        ])

    return "Stopped & Saved ✅"






@app.route("/data")
def data():
    student = request.args.get("student")
    if not student or student not in students:
        return jsonify({})

    s = students[student]

    return jsonify({
        "presence": s["presence"],
        "engagement_time": s["engagement_time"],
        "engagement": s["engagement_score"],
        "engagement_level": s["engagement_level"],
        "attention": s["attention_score"],
        "movement": s["movement"],
        "attendance": s["attendance"],
        "student_name": student
    })



@app.route("/faculty")
def faculty_dashboard():
    if "user" not in session or session.get("role") != "faculty":
        return redirect("/login")
    records = []

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                records.append(row)

    return render_template_string(FACULTY_HTML, records=records)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

from flask import request

@app.route("/metrics", methods=["POST"])
def metrics():
    data = request.json
    student = data.get("student")

    if not student or student not in students:
        return "INVALID STUDENT", 400

    s = students[student]

    if not s["running"]:
        return "STOPPED"

    now = time.time()

    if s["last_metric_time"] is None:
        s["last_metric_time"] = now
        return "OK"

    if now - s["last_metric_time"] < 1:
        return "OK"

    s["last_metric_time"] = now

    # ❌ NO FACE → STOP COUNTING
    if not data.get("face", False):
        s["movement"] = "No Face ❌"
        return "NO_FACE"

    # ✅ FACE PRESENT
    s["presence"] += 1
    s["attendance"] = "Present ✅" if s["presence"] >= ATTENDANCE_THRESHOLD else "Absent ❌"

    ear = data["ear"]
    mar = data["mar"]
    head = data["head"]

    attentive = ear > 0.22 and head < 0.3
    engaged = attentive and mar < 0.6

    if attentive:
        s["attention_time"] += 1
    if engaged:
        s["engagement_time"] += 1

    s["attention_score"] = int((s["attention_time"] / s["presence"]) * 100)
    s["engagement_score"] = int((s["engagement_time"] / s["presence"]) * 100)

    s["engagement_level"] = classify_engagement(s["engagement_score"])
    s["movement"] = "Engaged 🟢" if engaged else "Distracted 🔴"

    return "OK"



# ================= RUN =================
if __name__=="__main__":
  app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)

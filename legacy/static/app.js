// Global State
let currentUser = null;
let currentHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    checkCurrentUser();
    fetchStats();
});

async function checkCurrentUser() {
    try {
        const res = await fetch("/api/me");
        const data = await res.json();
        currentUser = data.user;
        updateUIState();
    } catch (e) {
        console.error("Failed to check auth state:", e);
    }
}

function updateUIState() {
    const authSection = document.getElementById("authSection");
    const dashboardSection = document.getElementById("dashboardSection");
    const userProfileSection = document.getElementById("userProfileSection");

    if (currentUser) {
        authSection.style.display = "none";
        dashboardSection.style.display = "block";

        userProfileSection.innerHTML = `
            <div class="user-profile-info">
                <div class="user-avatar">${currentUser.username.substring(0, 2).toUpperCase()}</div>
                <div>
                    <div style="font-weight: 600; font-size: 14px;">${currentUser.full_name}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${currentUser.email}</div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="handleLogout()" style="margin-left: 12px;">
                    <i class="fa-solid fa-right-from-bracket"></i> Logout
                </button>
            </div>
        `;

        fetchHistory();
        fetchStats();
    } else {
        authSection.style.display = "flex";
        dashboardSection.style.display = "none";
        userProfileSection.innerHTML = `
            <div style="font-size: 13px; color: var(--text-muted);">
                <i class="fa-solid fa-user-lock"></i> Guest Mode
            </div>
        `;
    }
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const loginTabBtn = document.getElementById("loginTabBtn");
    const registerTabBtn = document.getElementById("registerTabBtn");

    if (tab === "login") {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
        loginTabBtn.classList.add("active");
        registerTabBtn.classList.remove("active");
    } else {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        registerTabBtn.classList.add("active");
        loginTabBtn.classList.remove("active");
    }
}

function fillDemoCredentials() {
    document.getElementById("loginUsername").value = "demo";
    document.getElementById("loginPassword").value = "demo123";
}

async function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById("loginUsername").value.trim();
    const p = document.getElementById("loginPassword").value.trim();

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (res.ok) {
            currentUser = data.user;
            updateUIState();
        } else {
            alert(data.error || "Login failed");
        }
    } catch (err) {
        alert("Server error during login");
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const fullName = document.getElementById("regFullName").value.trim();
    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value.trim();

    try {
        const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ full_name: fullName, username, email, password })
        });
        const data = await res.json();
        if (res.ok) {
            currentUser = data.user;
            updateUIState();
        } else {
            alert(data.error || "Registration failed");
        }
    } catch (err) {
        alert("Server error during registration");
    }
}

async function handleLogout() {
    await fetch("/api/logout", { method: "POST" });
    currentUser = null;
    updateUIState();
}

async function fetchStats() {
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        document.getElementById("statTotalVideos").textContent = data.total_videos_analyzed || 0;
        document.getElementById("statAccidentsFlagged").textContent = data.accidents_detected || 0;
        document.getElementById("statAvgFPS").textContent = (data.average_processing_fps || 0.0) + " FPS";
    } catch (e) {
        console.error("Failed to fetch stats:", e);
    }
}

function updateSelectedFileName(input) {
    const display = document.getElementById("selectedFileName");
    if (input.files && input.files[0]) {
        display.textContent = `Selected: ${input.files[0].name} (${(input.files[0].size / (1024 * 1024)).toFixed(2)} MB)`;
    } else {
        display.textContent = "";
    }
}

async function handleUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("videoFileInput");
    if (!fileInput.files || !fileInput.files[0]) {
        alert("Please select a video file first.");
        return;
    }

    const formData = new FormData();
    formData.append("video", fileInput.files[0]);

    const uploadBtn = document.getElementById("uploadBtn");
    const statusDiv = document.getElementById("processingStatus");
    uploadBtn.disabled = true;
    statusDiv.style.display = "flex";

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            alert("Video successfully processed and accident analysis complete!");
            document.getElementById("uploadForm").reset();
            document.getElementById("selectedFileName").textContent = "";
            fetchHistory();
            fetchStats();
            if (data.history_id) {
                viewAnalysis(data.history_id);
            }
        } else {
            alert(data.error || "Upload processing failed");
        }
    } catch (err) {
        alert("Error sending video to detection pipeline.");
    } finally {
        uploadBtn.disabled = false;
        statusDiv.style.display = "none";
    }
}

async function fetchHistory() {
    try {
        const res = await fetch("/api/history");
        const data = await res.json();
        currentHistory = data.history || [];
        renderHistoryTable();
    } catch (e) {
        console.error("Failed to fetch history:", e);
    }
}

function renderHistoryTable() {
    const tbody = document.getElementById("historyTableBody");
    if (!currentHistory || currentHistory.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 30px;">
                    No uploaded videos found in history. Upload a video above to test detection.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = currentHistory.map((item) => {
        const isCrash = item.accident_detected;
        const statusBadge = isCrash
            ? `<span class="badge badge-red"><i class="fa-solid fa-triangle-exclamation"></i> ACCIDENT DETECTED</span>`
            : `<span class="badge badge-green"><i class="fa-solid fa-circle-check"></i> NORMAL TRAFFIC</span>`;
        
        const detTime = isCrash && item.first_accident_time_sec !== null
            ? `${item.first_accident_time_sec.toFixed(2)}s`
            : "N/A";

        return `
            <tr>
                <td>#${item.id}</td>
                <td><strong>${escapeHtml(item.original_filename)}</strong></td>
                <td>${item.upload_time ? item.upload_time.substring(0, 16) : "Just now"}</td>
                <td>${item.total_frames || 0} frames</td>
                <td>${statusBadge}</td>
                <td><span style="font-weight:700; color: ${isCrash ? '#ef4444' : '#10b981'}">${item.max_score}</span></td>
                <td>${detTime}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="viewAnalysis(${item.id})">
                        <i class="fa-solid fa-chart-line"></i> View Analysis
                    </button>
                    ${item.csv_path ? `
                        <a href="/media/${item.csv_path}" download class="btn btn-secondary btn-sm" title="Download CSV Log">
                            <i class="fa-solid fa-file-csv"></i> CSV
                        </a>
                    ` : ""}
                </td>
            </tr>
        `;
    }).join("");
}

async function viewAnalysis(historyId) {
    try {
        const res = await fetch(`/api/video/${historyId}`);
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || "Failed to load video details");
            return;
        }

        const record = data.record;
        const details = data.details || {};
        const modalBody = document.getElementById("modalBody");

        const videoSrc = record.annotated_path ? `/media/${record.annotated_path}` : "";

        modalBody.innerHTML = `
            <div style="margin-bottom: 20px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>${escapeHtml(record.original_filename)}</h3>
                    <div>
                        ${record.accident_detected
                            ? `<span class="badge badge-red" style="font-size:14px;"><i class="fa-solid fa-triangle-exclamation"></i> ACCIDENT CONFIRMED AT ${record.first_accident_time_sec ? record.first_accident_time_sec.toFixed(2) : 0}s</span>`
                            : `<span class="badge badge-green" style="font-size:14px;"><i class="fa-solid fa-circle-check"></i> NO ACCIDENT DETECTED</span>`
                        }
                    </div>
                </div>
            </div>

            <div class="modal-video-container">
                <video controls autoplay src="${videoSrc}">
                    Your browser does not support HTML5 video playback.
                </video>
            </div>

            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:16px; margin-bottom:24px;">
                <div class="glass-card" style="margin:0; padding:16px;">
                    <span class="stat-label">Max Collision Score</span>
                    <h3 style="color:${record.accident_detected ? '#ef4444' : '#10b981'}">${record.max_score}</h3>
                </div>
                <div class="glass-card" style="margin:0; padding:16px;">
                    <span class="stat-label">Total Frames Processed</span>
                    <h3>${record.total_frames} frames</h3>
                </div>
                <div class="glass-card" style="margin:0; padding:16px;">
                    <span class="stat-label">Video FPS</span>
                    <h3>${record.video_fps ? record.video_fps.toFixed(1) : 30.0} FPS</h3>
                </div>
                <div class="glass-card" style="margin:0; padding:16px;">
                    <span class="stat-label">Pipeline Processing Speed</span>
                    <h3>${record.processing_fps ? record.processing_fps.toFixed(2) : 0} FPS</h3>
                </div>
            </div>

            <div style="text-align:right;">
                <a href="/media/${record.csv_path}" download class="btn btn-secondary">
                    <i class="fa-solid fa-download"></i> Download Complete CSV Results Log
                </a>
            </div>
        `;

        document.getElementById("analysisModal").style.display = "flex";
    } catch (e) {
        console.error("Error opening analysis modal:", e);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

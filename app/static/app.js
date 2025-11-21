// API Base URL
const API_BASE = "http://localhost:8000";

// Global state
let currentUserId = null;

// Utility Functions
function showResult(elementId, message, isSuccess) {
  const resultEl = document.getElementById(elementId);
  resultEl.textContent = message;
  resultEl.className = `result show ${isSuccess ? "success" : "error"}`;

  setTimeout(() => {
    resultEl.classList.remove("show");
  }, 5000);
}

function formatTimestamp(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

// User Management
async function registerUser() {
  const username = document.getElementById("username").value.trim();

  if (!username) {
    showResult("registerResult", "Please enter a username", false);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }),
    });

    const data = await response.json();

    if (response.ok) {
      showResult(
        "registerResult",
        `User registered successfully! ID: ${data.user_id}`,
        true
      );
      document.getElementById("registerForm").reset();
      await loadUsers();
    } else {
      showResult("registerResult", data.error || "Registration failed", false);
    }
  } catch (error) {
    showResult("registerResult", "Network error: " + error.message, false);
  }
}

async function loadUsers() {
  try {
    const response = await fetch(`${API_BASE}/users`);
    const data = await response.json();

    const usersList = document.getElementById("usersList");

    if (data.users && data.users.length > 0) {
      usersList.innerHTML = data.users
        .map(
          (user) => `
                <div class="user-card">
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                        <div class="user-id">ID: ${user.id}</div>
                    </div>
                    <button class="btn-icon" onclick="selectUser(${user.id}, '${user.username}')" title="Select User">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 6L9 17l-5-5"/>
                        </svg>
                    </button>
                </div>
            `
        )
        .join("");
    } else {
      usersList.innerHTML = `
                <div class="empty-state">
                    <h3>No users yet</h3>
                    <p>Register a new user to get started</p>
                </div>
            `;
    }
  } catch (error) {
    console.error("Failed to load users:", error);
  }
}

function selectUser(userId, username) {
  currentUserId = userId;
  document.getElementById(
    "selectedUserId"
  ).textContent = `Selected: ${username} (ID: ${userId})`;
  document.getElementById("uploadUserId").value = userId;
  document.getElementById("viewFilesUserId").value = userId;
  document.getElementById("senderUserId").value = userId;
  loadUserFiles(userId);
}

// File Management
async function uploadFile() {
  const userId = document.getElementById("uploadUserId").value;
  const fileInput = document.getElementById("fileUpload");
  const file = fileInput.files[0];

  if (!userId || !file) {
    showResult("uploadResult", "Please select a user and a file", false);
    return;
  }

  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      showResult(
        "uploadResult",
        `File uploaded successfully! File ID: ${data.file_id}`,
        true
      );
      fileInput.value = "";
      updateFileName();
      await loadUserFiles(userId);
      await loadBlockchain();
    } else {
      showResult("uploadResult", data.error || "Upload failed", false);
    }
  } catch (error) {
    showResult("uploadResult", "Network error: " + error.message, false);
  }
}

function updateFileName() {
  const fileInput = document.getElementById("fileUpload");
  const label = document.querySelector(".file-input-label span");

  if (fileInput.files.length > 0) {
    label.textContent = fileInput.files[0].name;
  } else {
    label.textContent = "Click or drag to upload";
  }
}

async function loadUserFiles(userId) {
  if (!userId) return;

  try {
    const response = await fetch(`${API_BASE}/files/${userId}`);
    const data = await response.json();

    const filesList = document.getElementById("filesList");

    if (data.files && data.files.length > 0) {
      filesList.innerHTML = data.files
        .map(
          (file) => `
                <div class="file-card">
                    <div class="file-info">
                        <div class="file-name">${file.filename}</div>
                        <div class="file-meta">File ID: ${
                          file.id
                        } • Uploaded: ${formatTimestamp(file.uploaded_at)}</div>
                    </div>
                    <div class="file-actions">
                        <button class="btn-download" onclick="downloadFile(${
                          file.id
                        }, '${file.filename}')">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Download
                        </button>
                    </div>
                </div>
            `
        )
        .join("");
    } else {
      filesList.innerHTML = `
                <div class="empty-state">
                    <h3>No files yet</h3>
                    <p>Upload a file to get started</p>
                </div>
            `;
    }
  } catch (error) {
    console.error("Failed to load files:", error);
  }
}

async function downloadFile(fileId, filename) {
  try {
    const response = await fetch(`${API_BASE}/download/${fileId}`);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } else {
      const data = await response.json();
      alert("Download failed: " + (data.error || "Unknown error"));
    }
  } catch (error) {
    alert("Network error: " + error.message);
  }
}

// File Sharing
async function shareFile() {
  const fileId = document.getElementById("shareFileId").value;
  const senderId = document.getElementById("senderUserId").value;
  const recipientId = document.getElementById("recipientUserId").value;

  if (!fileId || !senderId || !recipientId) {
    showResult("shareResult", "Please fill in all fields", false);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/share`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        file_id: parseInt(fileId),
        sender_user_id: parseInt(senderId),
        recipient_user_id: parseInt(recipientId),
      }),
    });

    const data = await response.json();

    if (response.ok) {
      showResult("shareResult", "File shared successfully!", true);
      document.getElementById("shareForm").reset();
    } else {
      showResult("shareResult", data.error || "Sharing failed", false);
    }
  } catch (error) {
    showResult("shareResult", "Network error: " + error.message, false);
  }
}

// Blockchain
async function loadBlockchain() {
  try {
    const response = await fetch(`${API_BASE}/chain`);
    const data = await response.json();

    if (data.chain) {
      // Update status
      document.getElementById("chainLength").textContent = data.length;
      document.getElementById("chainValid").textContent = data.valid
        ? "Valid"
        : "Invalid";

      // Update blocks
      const blocksList = document.getElementById("blocksList");
      blocksList.innerHTML = data.chain
        .map(
          (block) => `
                <div class="block-card">
                    <div class="block-header">
                        <span class="block-index">Block #${block.index}</span>
                        <span class="block-timestamp">${formatTimestamp(
                          block.timestamp
                        )}</span>
                    </div>
                    <div class="block-data">
                        <div class="block-field">
                            <span class="block-label">Hash:</span>
                            <span class="block-value">${block.hash}</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">Previous Hash:</span>
                            <span class="block-value">${
                              block.previous_hash
                            }</span>
                        </div>
                        ${
                          block.data
                            ? `
                        <div class="block-field">
                            <span class="block-label">File ID:</span>
                            <span class="block-value">${
                              block.data.file_id
                            }</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">User ID:</span>
                            <span class="block-value">${
                              block.data.user_id
                            }</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">Filename:</span>
                            <span class="block-value">${
                              block.data.filename
                            }</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">AES Key (encrypted):</span>
                            <span class="block-value">${
                              block.data.aes_key_encrypted
                                ? block.data.aes_key_encrypted.substring(
                                    0,
                                    50
                                  ) + "..."
                                : "N/A"
                            }</span>
                        </div>
                        `
                            : ""
                        }
                    </div>
                </div>
            `
        )
        .join("");

      // Calculate total blocks
      document.getElementById("totalBlocks").textContent = data.chain.length;
    }
  } catch (error) {
    console.error("Failed to load blockchain:", error);
  }
}

// Health Check
async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();

    if (data.status === "healthy") {
      console.log("API is healthy:", data);
    }
  } catch (error) {
    console.error("API health check failed:", error);
  }
}

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
  // Check API health
  await checkHealth();

  // Load initial data
  await loadUsers();
  await loadBlockchain();

  // Set up file input change handler
  document
    .getElementById("fileUpload")
    .addEventListener("change", updateFileName);

  // Set up form submissions
  document.getElementById("registerForm").addEventListener("submit", (e) => {
    e.preventDefault();
    registerUser();
  });

  document.getElementById("uploadForm").addEventListener("submit", (e) => {
    e.preventDefault();
    uploadFile();
  });

  document.getElementById("shareForm").addEventListener("submit", (e) => {
    e.preventDefault();
    shareFile();
  });

  // Refresh data periodically
  setInterval(async () => {
    if (currentUserId) {
      await loadUserFiles(currentUserId);
    }
    await loadBlockchain();
  }, 30000); // Every 30 seconds
});

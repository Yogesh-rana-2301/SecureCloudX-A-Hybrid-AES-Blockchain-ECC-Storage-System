// API Base URL - Auto-detect environment
const API_BASE =
  window.location.hostname === "localhost"
    ? "http://localhost:8000" // Local development
    : window.location.origin; // Production (same domain)

// Global state
let currentUserId = null;
let authToken = null;

// Helper function to get auth headers
function getAuthHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
}

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
  if (!timestamp) return "N/A";
  // Handle both seconds and milliseconds
  const date = new Date(timestamp > 10000000000 ? timestamp : timestamp * 1000);
  return isNaN(date.getTime()) ? "Invalid Date" : date.toLocaleString();
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

// User Management
async function registerUser() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  if (!username) {
    showResult("registerResult", "Please enter a username", false);
    return;
  }

  if (!password) {
    showResult("registerResult", "Please enter a password", false);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
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
      showResult(
        "registerResult",
        data.detail || data.error || "Registration failed",
        false
      );
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

async function selectUser(userId, username) {
  try {
    // Call login API to get authentication token
    const response = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json();

    currentUserId = userId;
    authToken = data.token;

    // Store in localStorage for persistence
    localStorage.setItem("currentUserId", userId);
    localStorage.setItem("currentUsername", username);
    localStorage.setItem("authToken", authToken);

    // Update UI
    document.getElementById(
      "selectedUserId"
    ).textContent = `Selected: ${username} (ID: ${userId})`;
    document.getElementById("uploadUserId").value = userId;
    document.getElementById("viewFilesUserId").value = userId;
    document.getElementById("senderUserId").value = userId;

    // Show user session in header
    document.getElementById("loggedInUser").textContent = `👤 ${username}`;
    document.getElementById("userSession").style.display = "flex";

    showResult("registerResult", `Logged in as ${username}`, true);
    loadUserFiles(userId);
  } catch (error) {
    showResult("registerResult", "Login failed: " + error.message, false);
  }
}

async function logoutUser() {
  try {
    // Call logout API
    if (authToken) {
      await fetch(`${API_BASE}/api/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    }
  } catch (error) {
    console.error("Logout error:", error);
  }

  currentUserId = null;
  authToken = null;
  localStorage.removeItem("currentUserId");
  localStorage.removeItem("currentUsername");
  localStorage.removeItem("authToken");

  document.getElementById("selectedUserId").textContent = "No user selected";
  document.getElementById("uploadUserId").value = "";
  document.getElementById("viewFilesUserId").value = "";
  document.getElementById("senderUserId").value = "";
  document.getElementById("userSession").style.display = "none";
  document.getElementById("loginBtn").style.display = "block";
  document.getElementById("filesList").innerHTML = "";

  showResult("registerResult", "Logged out successfully", true);
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

  if (!authToken) {
    showResult("uploadResult", "Please log in first", false);
    return;
  }

  const formData = new FormData();
  formData.append("owner_id", userId);
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
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
      showResult(
        "uploadResult",
        data.detail || data.error || "Upload failed",
        false
      );
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

  if (!authToken) {
    showResult("viewResult", "Please log in first", false);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/files/${userId}`, {
      headers: getAuthHeaders(),
    });
    const data = await response.json();

    const filesList = document.getElementById("filesList");

    // Combine owned files and shared files
    const allFiles = [];

    if (data.owned_files && data.owned_files.length > 0) {
      allFiles.push(
        ...data.owned_files.map((file) => ({
          ...file,
          type: "owned",
        }))
      );
    }

    if (data.shared_with_me && data.shared_with_me.length > 0) {
      allFiles.push(
        ...data.shared_with_me.map((file) => ({
          ...file,
          type: "shared",
        }))
      );
    }

    if (allFiles.length > 0) {
      filesList.innerHTML = allFiles
        .map(
          (file) => `
                <div class="file-card">
                    <div class="file-info">
                        <div class="file-name">
                            ${file.filename}
                            ${
                              file.type === "shared"
                                ? '<span class="badge-shared">Shared</span>'
                                : ""
                            }
                        </div>
                        <div class="file-meta">File ID: ${file.id} • ${
            file.type === "shared"
              ? "Shared by User " + file.owner_id
              : "Uploaded"
          }: ${formatTimestamp(file.uploaded_at || file.shared_at)}</div>
                    </div>
                    <div class="file-actions">
                        <button class="btn-download" onclick="downloadFile(${
                          file.id
                        }, '${file.filename}', ${userId})">
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

async function downloadFile(fileId, filename, userId) {
  // Use the provided userId or fall back to currentUserId
  const downloadUserId = userId || currentUserId;

  if (!downloadUserId) {
    alert("Please select a user first (click on a user from the list)");
    return;
  }

  if (!authToken) {
    alert("Please log in first");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/download/${fileId}`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

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
      alert(
        "Download failed: " + (data.detail || data.error || "Unknown error")
      );
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

  if (!authToken) {
    showResult("shareResult", "Please log in first", false);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/share`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        file_id: parseInt(fileId),
        owner_id: parseInt(senderId),
        recipient_id: parseInt(recipientId),
      }),
    });

    const data = await response.json();

    if (response.ok) {
      showResult("shareResult", "File shared successfully!", true);
      document.getElementById("shareForm").reset();
    } else {
      showResult(
        "shareResult",
        data.detail || data.error || "Sharing failed",
        false
      );
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
      document.getElementById("chainValid").textContent = data.is_valid
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
                          block.data && block.data.filename
                            ? `
                        <div class="block-field">
                            <span class="block-label">Owner ID:</span>
                            <span class="block-value">${
                              block.data.owner_id || "N/A"
                            }</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">Filename:</span>
                            <span class="block-value">${
                              block.data.filename || "N/A"
                            }</span>
                        </div>
                        <div class="block-field">
                            <span class="block-label">Action:</span>
                            <span class="block-value">${
                              block.data.action || "upload"
                            }</span>
                        </div>
                        ${
                          block.data.recipient_id
                            ? `
                        <div class="block-field">
                            <span class="block-label">Recipient ID:</span>
                            <span class="block-value">${block.data.recipient_id}</span>
                        </div>
                        `
                            : ""
                        }
                        `
                            : block.data && block.data.message
                            ? `
                        <div class="block-field">
                            <span class="block-label">Message:</span>
                            <span class="block-value">${block.data.message}</span>
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
  // Restore user session if exists
  const savedUserId = localStorage.getItem("currentUserId");
  const savedUsername = localStorage.getItem("currentUsername");
  const savedToken = localStorage.getItem("authToken");

  if (savedUserId && savedUsername && savedToken) {
    currentUserId = parseInt(savedUserId);
    authToken = savedToken;
    document.getElementById("loggedInUser").textContent = `👤 ${savedUsername}`;
    document.getElementById("userSession").style.display = "flex";
    document.getElementById("loginBtn").style.display = "none";
    document.getElementById(
      "selectedUserId"
    ).textContent = `Selected: ${savedUsername} (ID: ${savedUserId})`;
    document.getElementById("uploadUserId").value = savedUserId;
    document.getElementById("viewFilesUserId").value = savedUserId;
    document.getElementById("senderUserId").value = savedUserId;
    await loadUserFiles(savedUserId);
  }

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

// Login Modal Functions
async function showLoginModal() {
  const modal = document.getElementById("loginModal");
  modal.style.display = "flex";

  // Clear login form
  document.getElementById("loginForm").reset();
  document.getElementById("loginResult").textContent = "";
  document.getElementById("loginResult").className = "result";
}

function closeLoginModal() {
  document.getElementById("loginModal").style.display = "none";
  document.getElementById("loginForm").reset();
}

async function loginUser(event) {
  event.preventDefault();

  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;

  if (!username || !password) {
    showResult("loginResult", "Please enter username and password", false);
    return;
  }

  try {
    // Call login API to get authentication token
    const response = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Login failed");
    }

    currentUserId = data.user_id;
    authToken = data.token;

    // Store in localStorage for persistence
    localStorage.setItem("currentUserId", data.user_id);
    localStorage.setItem("currentUsername", data.username);
    localStorage.setItem("authToken", authToken);

    // Update UI
    document.getElementById("loggedInUser").textContent = `👤 ${data.username}`;
    document.getElementById("userSession").style.display = "flex";
    document.getElementById("loginBtn").style.display = "none";
    document.getElementById(
      "selectedUserId"
    ).textContent = `Selected: ${data.username} (ID: ${data.user_id})`;
    document.getElementById("uploadUserId").value = data.user_id;
    document.getElementById("viewFilesUserId").value = data.user_id;
    document.getElementById("senderUserId").value = data.user_id;

    // Close modal and load user files
    closeLoginModal();
    showResult("loginResult", `Logged in as ${data.username}`, true);
    await loadUserFiles(data.user_id);

    // Scroll to files section
    document.getElementById("files").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showResult("loginResult", "Login failed: " + error.message, false);
  }
}

// Close modal when clicking outside
window.onclick = function (event) {
  const modal = document.getElementById("loginModal");
  if (event.target === modal) {
    closeLoginModal();
  }
};

// Filter users in login modal

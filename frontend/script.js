const BACKEND_URL = "http://localhost:8000"; // Change this to your deployed backend URL if needed

let uploadedFilename = "";

// Upload PDF
const uploadForm = document.getElementById("uploadForm");
const uploadStatus = document.getElementById("uploadStatus");
const qaSection = document.getElementById("qaSection");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(uploadForm);

  uploadStatus.innerText = "Uploading...";

  try {
    const response = await fetch(`${BACKEND_URL}/upload/`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Upload failed");

    const data = await response.json();
    uploadedFilename = data.file_id;
    uploadStatus.innerHTML = `✅ Uploaded <strong>${uploadedFilename}</strong> successfully.`;
    qaSection.style.display = "block";
  } catch (err) {
    uploadStatus.innerText = "❌ Upload failed.";
    console.error(err);
  }
});

// Ask Question
async function askQuestion() {
  const question = document.getElementById("questionInput").value.trim();
  const answerDisplay = document.getElementById("answerDisplay");

  if (!question) return;

  answerDisplay.innerHTML = "⏳ Getting answer...";

  try {
    const formData = new URLSearchParams();
    formData.append("question", question);
    formData.append("file_id", uploadedFilename);

    const response = await fetch(`${BACKEND_URL}/ask/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    if (!response.ok) throw new Error("Request failed");

    const data = await response.json();
    answerDisplay.innerText = data.answer || "No answer found.";
  } catch (err) {
    answerDisplay.innerText = "❌ Error getting answer.";
    console.error(err);
  }
}

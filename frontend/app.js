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
    const response = await fetch("/upload_pdf", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    uploadedFilename = data.filename;
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
    const response = await fetch("/ask_question", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        filename_filter: uploadedFilename,
      }),
    });

    const data = await response.json();
    answerDisplay.innerText = data.answer || "No answer found.";
  } catch (err) {
    answerDisplay.innerText = "Error getting answer.";
    console.error(err);
  }
}

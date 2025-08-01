document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ script.js loaded"); // confirms fresh version is used

  const BACKEND_URL =
    window.location.hostname === "localhost"
      ? "http://localhost:8000"
      : window.location.origin;

  const AUTH_TOKEN = "HACKRX_DEMO_KEY"; // Match this to .env

  const runForm = document.getElementById("runForm");
  const urlInput = document.getElementById("urlInput");
  const questionsInput = document.getElementById("questionsInput");
  const resultDisplay = document.getElementById("resultDisplay");

  runForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // prevent page reload

    const url = urlInput.value.trim();
    const rawQuestions = questionsInput.value.trim();

    if (!url || !rawQuestions) {
      resultDisplay.innerText = "❗ Please enter both document URL and questions.";
      return;
    }

    const questions = rawQuestions.split("\n").filter(q => q.trim().length > 0);

    resultDisplay.innerText = "⏳ Processing...";

    try {
      const response = await fetch(`${BACKEND_URL}/hackrx/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${AUTH_TOKEN}`
        },
        body: JSON.stringify({
          url: url,
          questions: questions
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Request failed");
      }

      const data = await response.json();
      const answers = data.answers;

      resultDisplay.innerHTML = answers
        .map((ans, i) => `
          <p>
            <strong>Q${i + 1}:</strong> ${questions[i]}<br/>
            <strong>Answer:</strong> ${ans}
          </p>
        `)
        .join("<hr/>");

    } catch (err) {
      resultDisplay.innerText = "❌ Error: " + err.message;
      console.error(err);
    }
  });
});

const form = document.getElementById("ask-form");
const questionInput = document.getElementById("question");
const statusEl = document.getElementById("status");
const answerEl = document.getElementById("answer");
const sourcesEl = document.getElementById("sources");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  statusEl.textContent = "Thinking...";
  answerEl.innerHTML = "";
  sourcesEl.innerHTML = "";

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();

    if (!response.ok) {
      statusEl.textContent = data.error || "Something went wrong.";
      return;
    }

    statusEl.textContent = data.cached ? "(answered from cache)" : "";
    const rawHtml = marked.parse(data.answer || "");
    answerEl.innerHTML = DOMPurify.sanitize(rawHtml);
    answerEl.querySelectorAll("pre code").forEach((block) => hljs.highlightElement(block));

    (data.sources || []).forEach((source) => {
      const li = document.createElement("li");
      li.textContent = source;
      sourcesEl.appendChild(li);
    });
  } catch (err) {
    statusEl.textContent = "Network error.";
  }
});

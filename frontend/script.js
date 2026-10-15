// Works in all of these cases:
//  - opened directly from the file (file:///.../index.html)
//  - opened with VS Code Live Server (http://127.0.0.1:5500)
//  - opened through FastAPI (http://localhost:8000) or an ngrok/cloudflared link
const BACKEND_URL = "http://localhost:8000";

const isLocalFile = window.location.protocol === "file:";
const isLocalDevServer =
  ["localhost", "127.0.0.1"].includes(window.location.hostname) &&
  window.location.port !== "8000";

const API_BASE = isLocalFile || isLocalDevServer ? BACKEND_URL : "";

const form = document.getElementById("calc-form");
const yourNameInput = document.getElementById("your-name");
const crushNameInput = document.getElementById("crush-name");
const errorEl = document.getElementById("error");
const button = document.getElementById("calc-btn");
const resultEl = document.getElementById("result");
const scoreEl = document.getElementById("score");
const namesEl = document.getElementById("result-names");
const msgEl = document.getElementById("result-msg");
const historyList = document.getElementById("history-list");

const messages = [
  "Wow, this is a really strong match!",
  "The stars are lining up for you two.",
  "That's a seriously good score.",
  "Say hi. The numbers are on your side.",
];

function showError(text) {
  errorEl.textContent = text;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function countUp(target) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    scoreEl.textContent = target + "%";
    return;
  }
  const duration = 900;
  const start = performance.now();
  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    scoreEl.textContent = Math.round(t * target) + "%";
    if (t < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function showResult(data) {
  namesEl.textContent = data.your_name + " + " + data.crush_name;
  msgEl.textContent = messages[Math.floor(Math.random() * messages.length)];
  resultEl.hidden = false;
  resultEl.classList.remove("pop");
  void resultEl.offsetWidth; // restart animation
  resultEl.classList.add("pop");
  countUp(data.score);
}

function renderHistory(rows) {
  historyList.innerHTML = "";
  if (!rows.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "No matches yet. Calculate one above.";
    historyList.appendChild(li);
    return;
  }
  rows.forEach((row) => {
    const li = document.createElement("li");
    const names = document.createElement("span");
    names.className = "names";
    names.textContent = row.your_name + " + " + row.crush_name;
    const pct = document.createElement("span");
    pct.className = "pct";
    pct.textContent = row.score + "%";
    li.append(names, pct);
    historyList.appendChild(li);
  });
}

async function loadHistory() {
  try {
    const res = await fetch(API_BASE + "/api/results?limit=10");
    if (!res.ok) throw new Error();
    renderHistory(await res.json());
  } catch (e) {
    /* history is optional; ignore failures */
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const yourName = yourNameInput.value.trim();
  const crushName = crushNameInput.value.trim();

  if (!yourName || !crushName) {
    showError("Enter both names to calculate.");
    return;
  }

  button.disabled = true;
  button.textContent = "Calculating...";

  try {
    const res = await fetch(API_BASE + "/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ your_name: yourName, crush_name: crushName }),
    });

    if (!res.ok) {
      let detail = "Something went wrong. Try again.";
      try {
        const body = await res.json();
        if (typeof body.detail === "string") detail = body.detail;
      } catch (e) {}
      throw new Error(detail);
    }

    const data = await res.json();
    showResult(data);
    loadHistory();
  } catch (err) {
    showError(err.message || "Can't reach the server. Is it running?");
  } finally {
    button.disabled = false;
    button.textContent = "Calculate";
  }
});

loadHistory();
/* =====================================================================
   LibQuery — script.js
   Handles the "Generate Query" button click:
     1. Reads the question from the textarea.
     2. Sends it to the FastAPI backend (POST /query).
     3. Shows the SQL, explanation, and result table — or a clear
        error message if anything went wrong.
===================================================================== */

// Change this if your backend runs on a different host/port.
const API_BASE_URL = "http://127.0.0.1:8000";

// Grab all the DOM elements we need up front.
const questionInput = document.getElementById("question-input");
const generateBtn = document.getElementById("generate-btn");
const loadingIndicator = document.getElementById("loading-indicator");

const errorCard = document.getElementById("error-card");
const errorMessage = document.getElementById("error-message");

const sqlCard = document.getElementById("sql-card");
const sqlOutput = document.getElementById("sql-output");

const explanationCard = document.getElementById("explanation-card");
const explanationOutput = document.getElementById("explanation-output");

const resultsCard = document.getElementById("results-card");
const resultsMeta = document.getElementById("results-meta");
const resultsThead = document.getElementById("results-thead");
const resultsTbody = document.getElementById("results-tbody");

// Hides every result/error panel — called before each new request.
function hideAllPanels() {
  errorCard.classList.add("hidden");
  sqlCard.classList.add("hidden");
  explanationCard.classList.add("hidden");
  resultsCard.classList.add("hidden");
}

// Shows a clear, human-readable error message in the error panel.
function showError(message) {
  errorMessage.textContent = message;
  errorCard.classList.remove("hidden");
}

// Renders the SQL query text.
function showSql(sql) {
  if (!sql) return;
  sqlOutput.textContent = sql;
  sqlCard.classList.remove("hidden");
}

// Renders the plain-English explanation.
function showExplanation(explanation) {
  if (!explanation) return;
  explanationOutput.textContent = explanation;
  explanationCard.classList.remove("hidden");
}

// Renders the result rows as an HTML table. Handles the "no rows" case.
function showResults(data) {
  resultsThead.innerHTML = "";
  resultsTbody.innerHTML = "";

  if (!data || data.length === 0) {
    resultsMeta.textContent = "0 rows returned.";
    resultsCard.classList.remove("hidden");
    return;
  }

  resultsMeta.textContent = `${data.length} row${data.length === 1 ? "" : "s"} returned.`;

  // Build the header row from the keys of the first result object.
  const columns = Object.keys(data[0]);
  const headerRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  resultsThead.appendChild(headerRow);

  // Build one table row per result.
  data.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      const value = row[col];
      td.textContent = value === null || value === undefined ? "—" : value;
      tr.appendChild(td);
    });
    resultsTbody.appendChild(tr);
  });

  resultsCard.classList.remove("hidden");
}

// Toggles the button/loading state while a request is in flight.
function setLoading(isLoading) {
  generateBtn.disabled = isLoading;
  loadingIndicator.classList.toggle("hidden", !isLoading);
}

async function generateQuery() {
  const question = questionInput.value.trim();

  hideAllPanels();

  // Client-side check for an empty question (matches backend validation).
  if (!question) {
    showError("Please enter a question before generating a query.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      // The backend returned an HTTP-level error (rare, but handle it).
      showError(`Server returned an error (status ${response.status}). Please try again.`);
      return;
    }

    const result = await response.json();

    // Always show SQL/explanation if they were generated, even on failure,
    // so the user can see what the AI attempted.
    showSql(result.sql);
    showExplanation(result.explanation);

    if (result.success) {
      showResults(result.data);
    } else {
      showError(result.error || "An unknown error occurred.");
    }
  } catch (err) {
    // This catches network failures, e.g. the backend isn't running at all.
    showError(
      "Could not reach the LibQuery backend. Make sure the FastAPI server " +
      "is running at " + API_BASE_URL + "."
    );
  } finally {
    setLoading(false);
  }
}

generateBtn.addEventListener("click", generateQuery);

// Allow Ctrl+Enter / Cmd+Enter inside the textarea to trigger generation.
questionInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    generateQuery();
  }
});
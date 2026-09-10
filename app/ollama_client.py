import json
import re
import requests

from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from database import DATABASE_SCHEMA


class OllamaConnectionError(Exception):
    """Raised when Ollama cannot be reached (e.g. not running)."""
    pass


class OllamaModelError(Exception):
    """Raised when the requested model is not available / not pulled."""
    pass


def build_prompt(question: str) -> str:
    """
    Builds the full prompt sent to Llama 3.2. The prompt is strict about
    the rules so the model behaves predictably for a beginner project.
    """
    prompt = f"""You are a SQL generation assistant for a MySQL library database.

DATABASE SCHEMA (only use these tables and columns, do not invent any):
{DATABASE_SCHEMA}

STRICT RULES:
1. Generate ONLY MySQL-compatible SQL.
2. Generate ONLY SELECT queries. Never write INSERT, UPDATE, DELETE, DROP,
   ALTER, TRUNCATE, CREATE, REPLACE, GRANT, or REVOKE statements.
3. Use ONLY the tables and columns listed in the schema above. Do not
   invent table or column names.
4. Never modify the database in any way.
5. CRITICAL: If the question asks about an entity, table, or concept that
   is NOT present in the schema above (for example "employees", "staff",
   "authors table", "publishers", "fines", "reservations" — anything not
   literally listed), do NOT substitute the closest-sounding table and do
   NOT guess. Instead, set "sql" to an empty string "" and use
   "explanation" to state clearly, in plain English, that this database
   does not contain that information, naming what it DOES contain instead
   (books, members, categories, borrow records).
6. Return your answer STRICTLY as a JSON object with exactly two keys:
   "sql"          -> the generated SQL query as a single-line string, or ""
                      if the question cannot be answered from this schema
   "explanation"  -> a short, plain-English explanation of what the query
                      does, OR (if sql is "") why the question can't be
                      answered from this database
7. Do not include markdown code fences, comments, or any text outside
   the JSON object.

USER QUESTION:
"{question}"

Respond with ONLY the JSON object described above.
"""
    return prompt


def extract_json_from_text(text_response: str) -> dict:
    """
    Llama models sometimes wrap JSON in markdown fences or add extra text.
    This function extracts the first valid JSON object found in the text.
    """
    # Remove markdown code fences if present
    cleaned = text_response.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip(), flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned.strip()).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first {...} block using a regex search
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # If nothing worked, raise so the caller can show a clean error
    raise ValueError("Could not parse a valid JSON object from the AI response.")


def ask_llama(question: str) -> dict:
    """
    Sends the question to Ollama's /api/generate endpoint and returns a
    dictionary with keys "sql" and "explanation".

    Raises:
        OllamaConnectionError: if Ollama is not reachable (not running).
        OllamaModelError: if the model is not installed/found.
        ValueError: if the model's response could not be parsed as JSON.
    """
    prompt = build_prompt(question)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,       # we want the full response at once, not streamed chunks
        "format": "json",      # ask Ollama to constrain output to valid JSON
        "options": {
            "temperature": 0.1  # low temperature = more predictable, consistent SQL
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            "Could not connect to Ollama. Make sure Ollama is installed and "
            "running (try running 'ollama run llama3.2' in a terminal)."
        )
    except requests.exceptions.Timeout:
        raise OllamaConnectionError(
            "Ollama took too long to respond. The model may still be loading; "
            "please try again in a moment."
        )

    if response.status_code == 404:
        raise OllamaModelError(
            f"Model '{OLLAMA_MODEL}' was not found. Run 'ollama pull {OLLAMA_MODEL}' "
            "to install it first."
        )

    if response.status_code != 200:
        raise OllamaConnectionError(
            f"Ollama returned an unexpected error (status {response.status_code})."
        )

    response_data = response.json()
    raw_text = response_data.get("response", "")

    if not raw_text:
        raise ValueError("Ollama returned an empty response.")

    parsed = extract_json_from_text(raw_text)

    sql = parsed.get("sql", "").strip()
    explanation = parsed.get("explanation", "").strip()

    if not sql:
        # The model deliberately left sql empty — this means the question
        # asked about something not present in our schema (see rule 5 in
        # build_prompt), e.g. "employees" when only "members" exists.
        # Surface the model's own explanation as the error message.
        raise ValueError(
            explanation or
            "This question doesn't match any information in the library "
            "database (books, members, categories, or borrow records)."
        )

    return {"sql": sql, "explanation": explanation or "No explanation was provided."}


def summarize_data(question: str, data: list) -> str:
    """
    Sends the actual query RESULTS (not the SQL) back to Llama 3.2 and asks
    for a short, plain-English summary of what the data shows, in direct
    response to the user's original question.

    This is called AFTER the query has been executed, so it can describe
    real numbers/names from the result set (e.g. "3 books are currently
    available: ...") rather than just describing what the query does.

    If anything goes wrong here, an empty string is returned instead of
    raising an error — a missing result summary should never break the
    whole /query response, since the SQL/explanation/data are already valid.
    """
    if not data:
        return "The query ran successfully but returned no matching rows."

    # Limit how many rows we send back to the model — keeps the prompt small
    # and the summary fast, even if the query returned hundreds of rows.
    sample = data[:20]

    prompt = f"""You are summarizing the result of a database query for a non-technical user.

USER'S ORIGINAL QUESTION:
"{question}"

QUERY RESULT (JSON array, {len(data)} total row(s), showing up to 20 below):
{json.dumps(sample, default=str)}

Write a short, plain-English summary that answers the user's question
directly, using this EXACT formatting style:
- If the result is a single number or fact, answer in ONE short sentence
  and nothing else.
- If the result lists multiple items (books, members, etc.), the FIRST
  line must be a one-sentence overview. Then each item must appear on
  its OWN LINE, starting with a real newline character followed by "- ".
  Never put more than one item on the same line, and never join items
  with " - " in the middle of a sentence.

Example of the required format for a list of 2 items:
There are 2 items matching your question.
- First item, with its key details here.
- Second item, with its key details here.

Rules:
- Mention concrete figures, titles, or names from the data — never say
  "the data shows" without stating what it actually shows.
- Do not mention SQL, tables, columns, or databases.
- Respond with ONLY the summary text in the exact format above — no JSON,
  no markdown headers, no code fences.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        if response.status_code != 200:
            return ""
        response_data = response.json()
        summary = response_data.get("response", "").strip()
        return normalize_bullet_formatting(summary)
    except (requests.exceptions.RequestException, ValueError):
        # Network issue, timeout, or bad JSON — just skip the summary
        # rather than failing the whole request.
        return ""


def normalize_bullet_formatting(text: str) -> str:
    """
    Safety net for when the model ignores the formatting instructions and
    runs bullet items together on one line (e.g. "... 9876543210. - Niveda
    Pillai, ...") instead of putting each on its own line.

    This converts any ". - " or ".- " pattern that appears mid-sentence
    into a real newline followed by "- ", so the frontend's bullet-list
    parser (which looks for lines starting with "- ") renders it correctly
    even when the AI's raw output doesn't use real newlines.
    """
    if not text:
        return text

    # Turn ". - Something" (period, optional space, hyphen, space) into
    # a real line break before the bullet, wherever it occurs in the text.
    normalized = re.sub(r"\.\s*-\s+", ".\n- ", text)

    return normalized.strip()
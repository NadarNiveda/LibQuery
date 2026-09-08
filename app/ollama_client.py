"""
ollama_client.py
-----------------
Handles all communication with the locally running Ollama server.

Ollama must already be installed and running the llama3.2 model:
    ollama pull llama3.2
    ollama run llama3.2   (or it will auto-start when called via API)

This module sends the user's natural-language question (plus the
database schema) to Llama 3.2 and asks it to return SQL + an explanation.
"""

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
5. Return your answer STRICTLY as a JSON object with exactly two keys:
   "sql"          -> the generated SQL query as a single-line string
   "explanation"  -> a short, plain-English explanation of what the query does
6. Do not include markdown code fences, comments, or any text outside
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
        raise ValueError("The AI did not return a SQL query.")

    return {"sql": sql, "explanation": explanation or "No explanation was provided."}
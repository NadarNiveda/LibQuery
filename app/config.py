"""
config.py
---------
Central place for all configuration values used across the LibQuery backend.

Keeping these values in one file means you only need to change your
MySQL username/password or Ollama settings in ONE place.
"""

import os
from dotenv import load_dotenv

# Loads variables from a .env file (in the project root) into the
# environment, if that file exists. This keeps real passwords out of
# the source code / out of git.
load_dotenv()

# ---------------------------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------------------------
# Format: mysql+pymysql://<username>:<password>@<host>/<database_name>
#
# The real value should live in a .env file (never committed to git):
#   DATABASE_URL=mysql+pymysql://root:mypassword123@localhost/library_db
#
# If no .env file / environment variable is found, this placeholder is
# used as a fallback so the app still starts (though it likely won't
# connect until you set a real value).
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost/library_db"
)

# ---------------------------------------------------------------------------
# OLLAMA CONFIGURATION
# ---------------------------------------------------------------------------
# URL of the local Ollama server (default installation URL/port).
OLLAMA_URL = "http://localhost:11434/api/generate"

# The model that must already be pulled locally using:
#   ollama pull llama3.2
OLLAMA_MODEL = "llama3.2"

# How long (in seconds) to wait for Ollama to respond before giving up.
OLLAMA_TIMEOUT = 60
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost/library_db"
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# The model that must already be pulled locally using:
#   ollama pull llama3.2
OLLAMA_MODEL = "llama3.2"

# How long (in seconds) to wait for Ollama to respond before giving up.
OLLAMA_TIMEOUT = 60
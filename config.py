import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
CURRICULUM_FILE = BASE_DIR / "jsonfiles" / "curriculum.json"
STUDENT_STATE_FILE = BASE_DIR / "jsonfiles" / "student_state.json"
SESSION_LOG_FILE = BASE_DIR / "jsonfiles" / "session_log.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
import os
from dotenv import load_dotenv
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "finops-lab-511007")
ENABLE_AI = os.getenv("ENABLE_AI", "false").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global")
IDLE_CPU_THRESHOLD = float(os.getenv("IDLE_CPU_THRESHOLD", "0.05"))
IDLE_LOOKBACK_DAYS = int(os.getenv("IDLE_LOOKBACK_DAYS", "7"))

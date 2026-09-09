import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent.emailer import send_email

if __name__ == "__main__":
    result = send_email(
        subject="Agentic OR email test",
        body="Success: the Agentic OR prototype can send email from this machine.",
        attachments=[],
    )
    print(result)

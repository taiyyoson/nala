import json
import os

from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

load_dotenv()

# Support both a file path (local) and inline JSON string (Render)
firebase_creds = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv(
    "FIREBASE_CREDENTIALS"
)

if not firebase_creds:
    raise ValueError(
        "Set FIREBASE_CREDENTIALS_PATH (file path) or FIREBASE_CREDENTIALS (JSON string)"
    )

if os.path.isfile(firebase_creds):
    cred = credentials.Certificate(firebase_creds)
else:
    cred = credentials.Certificate(json.loads(firebase_creds))

initialize_app(cred)

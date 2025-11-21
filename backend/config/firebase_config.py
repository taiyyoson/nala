import os

from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

load_dotenv()
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
initialize_app(cred)

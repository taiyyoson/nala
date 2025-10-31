import os
from firebase_admin import credentials, initialize_app
from dotenv import load_dotenv

load_dotenv()
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
initialize_app(cred)

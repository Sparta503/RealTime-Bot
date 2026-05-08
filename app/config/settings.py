from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('OPENROUTER_API_KEY', '')
BASE_URL = 'https://openrouter.ai/api/v1'
temperature = 0

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
cliente_ia = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("Modelos disponibles en tu cuenta:")
for modelo in cliente_ia.models.list():
    if "flash" in modelo.name:
        print(f"- {modelo.name}")
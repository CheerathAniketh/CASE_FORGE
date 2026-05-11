from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("\n" + "="*60)
print("🔍 CHECKING AVAILABLE GROQ MODELS")
print("="*60 + "\n")

try:
    models = client.models.list()
    
    print("Available models:\n")
    for model in models.data:
        print(f"  ✅ {model.id}")
    
    print("\n" + "="*60)
    print("Use one of these model IDs in your .env file")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ Error: {e}")

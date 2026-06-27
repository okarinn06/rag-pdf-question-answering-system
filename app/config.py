import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_groq_api_key() -> str:
    load_dotenv()
    res = os.getenv("GROQ_API_KEY").strip()
    return res

def has_groq_api_key() -> bool:
    key = get_groq_api_key()
    return bool(key != None)

GROQ_API_KEY = get_groq_api_key()
CHUNK_SIZE = int(500)
CHUNK_OVERLAP = int(50)
LLM_MODEL = "openai/gpt-oss-120b"
RETRIEVER_K = int(4)
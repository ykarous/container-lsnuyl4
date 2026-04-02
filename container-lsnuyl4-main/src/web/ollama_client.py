import os
from flask import g
from dotenv import load_dotenv
from logger import log
import ollama

load_dotenv(verbose=True)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")

OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"


def get_ollama_client():
    if "ollama" not in g:
        log.info(f"Connecting to Ollama at {OLLAMA_BASE_URL}")
        try:
            g.ollama = ollama.Client(host=OLLAMA_BASE_URL)
            return g.ollama
        except Exception as e:
            log.error(f"Failed to connect to Ollama: {e}")
            g.ollama = None
            return None
    return g.ollama


def close_ollama(e=None):
    log.info("close_ollama requested")
    ollama_client = g.pop("ollama", None)
    if ollama_client is not None:
        log.info("Ollama client cleanup done")
    else:
        log.info("Ollama client not initialized. No action taken.")


def list_models():
    client = get_ollama_client()
    if client is None:
        return []
    try:
        response = ollama.list()
        return response.get("models", [])
    except Exception as e:
        log.error(f"Error listing models: {e}")
        return []


def chat(model, messages):
    client = get_ollama_client()
    if client is None:
        return None
    try:
        response = client.chat(model=model, messages=messages)
        return response
    except Exception as e:
        log.error(f"Error chatting with model: {e}")
        return None


def generate(model, prompt):
    client = get_ollama_client()
    if client is None:
        return None
    try:
        response = client.generate(model=model, prompt=prompt)
        return response
    except Exception as e:
        log.error(f"Error generating with model: {e}")
        return None


def pull_model(model):
    client = get_ollama_client()
    if client is None:
        return None
    try:
        response = client.pull(model=model)
        return response
    except Exception as e:
        log.error(f"Error pulling model: {e}")
        return None


def check_ollama_health():
    client = get_ollama_client()
    if client is None:
        return False
    try:
        ollama.ps()
        return True
    except Exception as e:
        log.error(f"Ollama health check failed: {e}")
        return False

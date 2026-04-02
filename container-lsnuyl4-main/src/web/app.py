from flask import Flask, render_template, jsonify, request
from db import get_db, close_db
from ollama_client import (
    get_ollama_client,
    close_ollama,
    list_models,
    chat,
    generate,
    pull_model,
    check_ollama_health,
)
import sqlalchemy
from sqlalchemy import text
from logger import log
import psutil
import platform
import os

def get_system_info():
    print(f"--- Système ---")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    
    print(f"\n--- Processeur (CPU) ---")
    print(f"Modèle: {platform.processor()}")
    print(f"Cœurs physiques: {psutil.cpu_count(logical=False)}")
    print(f"Cœurs logiques: {psutil.cpu_count(logical=True)}")
    print(f"Fréquence: {psutil.cpu_freq().current}Mhz")

    print(f"\n--- Mémoire (RAM) ---")
    mem = psutil.virtual_memory()
    print(f"Totale: {mem.total / (1024**3):.2f} GB")
    print(f"Utilisée: {mem.used / (1024**3):.2f} GB")

    print(f"\n--- Disque ---")
    usage = psutil.disk_usage('/')
    print(f"Espace total: {usage.total / (1024**3):.2f} GB")

if __name__ == "__main__":
    get_system_info()

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.teardown_appcontext(close_ollama)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    log.info("Checking /health")
    db = get_db()
    health_status = {"status": "BAD", "database": "BAD", "ollama": "BAD"}
    try:
        result = db.execute(text("SELECT NOW()"))
        result = result.one()
        health_status["database"] = "OK"
        health_status["status"] = "OK"
        log.info(f"Database health OK: {result}")
    except sqlalchemy.exc.OperationalError as e:
        msg = f"sqlalchemy.exc.OperationalError: {e}"
        log.error(msg)
    except Exception as e:
        msg = f"Error performing database healthcheck: {e}"
        log.error(msg)

    if check_ollama_health():
        health_status["ollama"] = "OK"
    else:
        health_status["status"] = "PARTIAL"

    return jsonify(health_status)


@app.route("/ollama/models")
def ollama_models():
    log.info("Listing Ollama models")
    models = list_models()
    return jsonify({"models": models})


@app.route("/ollama/chat", methods=["POST"])
def ollama_chat():
    data = request.get_json()
    if not data or "model" not in data or "messages" not in data:
        return jsonify({"error": "Missing 'model' or 'messages' in request body"}), 400

    log.info(f"Chatting with model: {data['model']}")
    response = chat(data["model"], data["messages"])
    if response is None:
        return jsonify({"error": "Failed to get response from Ollama"}), 500

    return jsonify(response)


@app.route("/ollama/generate", methods=["POST"])
def ollama_generate():
    data = request.get_json()
    if not data or "model" not in data or "prompt" not in data:
        return jsonify({"error": "Missing 'model' or 'prompt' in request body"}), 400

    log.info(f"Generating with model: {data['model']}")
    response = generate(data["model"], data["prompt"])
    if response is None:
        return jsonify({"error": "Failed to get response from Ollama"}), 500

    return jsonify(response)


@app.route("/ollama/pull", methods=["POST"])
def ollama_pull():
    data = request.get_json()
    if not data or "model" not in data:
        return jsonify({"error": "Missing 'model' in request body"}), 400

    log.info(f"Pulling model: {data['model']}")
    response = pull_model(data["model"])
    if response is None:
        return jsonify({"error": "Failed to pull model from Ollama"}), 500

    return jsonify({"status": "success", "response": response})


@app.route("/ollama/health")
def ollama_health():
    log.info("Checking Ollama health")
    is_healthy = check_ollama_health()
    return jsonify({"status": "OK" if is_healthy else "BAD", "host": os.getenv("OLLAMA_HOST", "127.0.0.1"), "port": os.getenv("OLLAMA_PORT", "11434")})

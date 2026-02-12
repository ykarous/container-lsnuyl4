from flask import Flask, render_template
from db import get_db, close_db
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    log.info("Checking /health")
    db = get_db()
    health = "BAD"
    try:
        result = db.execute(text("SELECT NOW()"))
        result = result.one()
        health = "OK"
        log.info(f"/health reported OK including database connection: {result}")
    except sqlalchemy.exc.OperationalError as e:
        msg = f"sqlalchemy.exc.OperationalError: {e}"
        log.error(msg)
    except Exception as e:
        msg = f"Error performing healthcheck: {e}"
        log.error(msg)

    return health

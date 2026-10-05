import os
from functools import wraps

from flask import Flask, jsonify, request

from market import get_price
from paper_engine import load_state, save_state
from reports import daily_report
from config import SYMBOL

app = Flask(__name__)

API_TOKEN = os.getenv("TRADING_API_TOKEN")

if not API_TOKEN:
    raise RuntimeError("TRADING_API_TOKEN is not set")


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")

        if auth != f"Bearer {API_TOKEN}":
            return jsonify({"ok": False, "error": "Unauthorized"}), 401

        return fn(*args, **kwargs)

    return wrapper


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "paper-trader",
        "mode": "paper"
    })


@app.get("/status")
@require_auth
def status():
    return jsonify(load_state())


@app.get("/quote")
@require_auth
def quote():
    return jsonify(get_price(SYMBOL))


@app.get("/trades")
@require_auth
def trades():
    return jsonify(load_state().get("trades", []))


@app.get("/report")
@require_auth
def report():
    return jsonify({"report": daily_report()})


@app.post("/pause")
@require_auth
def pause():
    state = load_state()
    state["status"] = "paused"
    save_state(state)
    return jsonify({"ok": True, "status": "paused"})


@app.post("/resume")
@require_auth
def resume():
    state = load_state()
    state["status"] = "running"
    save_state(state)
    return jsonify({"ok": True, "status": "running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

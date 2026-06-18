"""Flask web UI + JSON API. LLM calls happen server-side only -- the API
key never reaches the browser.
"""
import logging
import re

from flask import Flask, jsonify, render_template, request

import config
import query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_SECRET_RE = re.compile(r"\b(sk|pk)-[A-Za-z0-9_-]{8,}\b")


def _scrub(message: str) -> str:
    """Strip anything that looks like an API key before it reaches a client."""
    return _SECRET_RE.sub("[REDACTED]", message)


@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def api_ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Missing 'question'"}), 400

    try:
        result = query.ask(question)
    except FileNotFoundError as e:
        return jsonify({"error": _scrub(str(e))}), 503
    except Exception:  # noqa: BLE001 -- never leak provider error details
        logger.exception("ask failed")
        return jsonify({"error": "Something went wrong answering that question."}), 500

    return jsonify(result)


@app.route("/api/sources")
def api_sources():
    try:
        return jsonify({"sources": query.list_sources()})
    except FileNotFoundError as e:
        return jsonify({"error": _scrub(str(e))}), 503


@app.route("/api/stats")
def api_stats():
    try:
        stats = query.index_stats()
        stats["cache"] = query.cache_stats()
        return jsonify(stats)
    except FileNotFoundError as e:
        return jsonify({"error": _scrub(str(e))}), 503


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=False)

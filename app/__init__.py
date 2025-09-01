import os
import logging
from flask import Flask, jsonify, g


def create_app() -> Flask:
    app = Flask(__name__)

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logFormatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    os.makedirs("/logs", exist_ok=True)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    # Console logger to keep stdout stream
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    root.addHandler(consoleHandler)

    app.logger.warning("Ayoooo")

    @app.before_request
    def before():
        app.logger.info("Incoming request")

    @app.after_request
    def after(resp):
        return resp

    @app.get("/")
    def home():
        return jsonify({"status": "ok", "time": g.timestamp}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)
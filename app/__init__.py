import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify, g, has_request_context, make_response

'''
Custom logging filter to populate dynamic field per request (remote_addr)
'''
class CustomLoggingFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.source_ip = getattr(g, "source_ip", "NA")
        else:
            record.source_ip = "-"
        return True

def create_app() -> Flask:
    app = Flask(__name__)

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logFormatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(source_ip)s] %(message)s")
    os.makedirs("/logs", exist_ok=True)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    # Console logger to keep stdout stream
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.addFilter(CustomLoggingFilter())
    root.addHandler(consoleHandler)

    # File logger
    fileHandler = logging.FileHandler("/logs/demo.log")
    fileHandler.setFormatter(logFormatter)
    root.addHandler(fileHandler)

    app.logger.warning("The app is a demo, no proper WSGI is implemented since it's not required")

    @app.before_request
    def before():
        g.source_ip = request.remote_addr
        g.start_time = time.time() * 1000
        g.timestamp = datetime.utcnow().isoformat() + "Z"
        app.logger.info("Incoming request")

    @app.after_request
    def after(resp):
        latency = int(round((time.time() * 1000) - g.start_time))
        app.logger.info("Processing ended with a latency of %dms", latency)
        return resp

    @app.get("/")
    def home():
        return jsonify({"status": "ok", "time": g.timestamp}), 200

    @app.get("/logs")
    def logs():
        try:
            with open('/logs/demo.log', 'r') as file:
                logs = file.read()
            resp = make_response(logs, 200)
            resp.mimetype = "text/plain"
            app.logger.info("Returning app logs")
            return resp
        except Exception as e:
            app.logger.error("Error while reading log file: %s", e)
        return jsonify({"error": "Cannot access log file"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)
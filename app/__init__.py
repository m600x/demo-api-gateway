import os
import logging
import json
import time
import requests
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, g, has_request_context, make_response

'''
Custom logging filter to populate dynamic field per request (request_id and remote_addr)
'''
class CustomLoggingFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, "request_id", "NA")
            record.source_ip = getattr(g, "source_ip", "NA")
        else:
            record.request_id = "-"
            record.source_ip = "-"
        return True

def create_app() -> Flask:
    app = Flask(__name__)

    '''
    Logger setup
    '''
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logFormatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(source_ip)s] [%(request_id)s] %(message)s")
    if os.path.exists("/.dockerenv"):
        logs_dir = "/logs"
    else:
        logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    # Console logger to keep stdout stream
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.addFilter(CustomLoggingFilter())
    root.addHandler(consoleHandler)

    # File logger
    fileHandler = logging.FileHandler(os.path.join(logs_dir, "demo.log"))
    fileHandler.setFormatter(logFormatter)
    root.addHandler(fileHandler)

    # Completion logger to keep an history of prompt
    completionLogger = logging.getLogger("completion")
    completionLogger.setLevel(logging.INFO)
    completionLogger.propagate = False
    completionHandler = logging.FileHandler(os.path.join(logs_dir, "completion.log"))
    completionLogger.addHandler(completionHandler)

    if not os.getenv("OLLAMA_URL", "").strip():
        app.logger.warning("No Ollama URL has been provided, the endpoint will not forward the request")
    app.logger.warning("The app is a demo, no proper WSGI is implemented since it's not required")

    '''
    Tagging the incoming request with global variable
    '''
    @app.before_request
    def before():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.source_ip = request.remote_addr
        g.start_time = time.time() * 1000
        g.timestamp = datetime.utcnow().isoformat() + "Z"
        app.logger.info("Incoming request")

    '''
    Marking the end of the request processing, compute the latency
    '''
    @app.after_request
    def after(resp):
        latency = int(round((time.time() * 1000) - g.start_time))
        if hasattr(g, "prompt"):
            completionLogger.info(json.dumps({
                "timestamp": g.timestamp,
                "origin":g.source_ip,
                "latency": latency,
                "prompt": g.prompt,
                "completion": g.completion
                }))
        app.logger.info("Processing ended with a latency of %dms", latency)
        return resp

    '''
    Handle root path, returning a simple response
    '''
    @app.get("/")
    def home():
        return jsonify({"status": "ok", "time": g.timestamp}), 200

    '''
    Serve the logs file as plain text
    '''
    @app.get("/logs")
    def logs():
        try:
            with open(os.path.join(logs_dir, "demo.log"), 'r') as file:
                logs = file.read()
            resp = make_response(logs, 200)
            resp.mimetype = "text/plain"
            app.logger.info("Returning app logs")
            return resp
        except Exception as e:
            app.logger.error("Error while reading log file: %s", e)
        return jsonify({"error": "Cannot access log file"}), 500

    '''
    Serve the completion history log file as plain text
    '''
    @app.get("/history")
    def history():
        try:
            with open(os.path.join(logs_dir, "completion.log"), 'r') as file:
                logs = file.read()
            resp = make_response(logs, 200)
            resp.mimetype = "text/plain"
            app.logger.info("Returning completion history")
            return resp
        except Exception as e:
            app.logger.error("Error while reading completion log file: %s", e)
        return jsonify({"error": "Cannot access completion log file"}), 500

    '''
    Handle POST on /completion.
    Return the LLM response or an altered prompt if unreachable
    '''
    @app.post("/completion")
    def completion():
        payload = request.get_json(silent=True) or {}
        content = payload.get("prompt", "")
        if not isinstance(content, str) or not content.strip():
            app.logger.error("The request doesn't contain a valid argument")
            return jsonify({"error": "Malformed or missing prompt argument"}), 400

        ollama_url = os.getenv("OLLAMA_URL", "").strip()
        if ollama_url:
            try:
                app.logger.info("Querying LLM with prompt: %s", content)
                r = requests.post(ollama_url, json={"model": "llama2", "stream": False, "prompt": content})
                r.raise_for_status()
                response = r.json()["response"]
                g.prompt = content
                g.completion = response
            except Exception as broken:
                app.logger.error("Error while forwarding to the LLM: %s", broken)
            return jsonify({"completion": response})

        # Fallback if no Ollama URL is provided, only alter the original prompt to simulate processing
        response = []
        for i, c in enumerate(content):
            if i % 2 == 0:
                response.append(c.lower())
            else:
                response.append(c.upper())
        return jsonify({"completion": "".join(response)})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)
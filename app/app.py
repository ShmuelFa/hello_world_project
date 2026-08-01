from flask import Flask, jsonify
import socket
import os

app = Flask(__name__)


@app.route("/")
def hello_world():
    return f"""
    <html>
        <head><title>Hello World - DevOps Pipeline</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 100px;">
            <h1>Hello World</h1>
            <p>Served by pod: {socket.gethostname()}</p>
            <p>Version: {os.environ.get('APP_VERSION', 'v1')}</p>
        </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

"""Entry point for running the Flask app as a module"""
from backend.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)


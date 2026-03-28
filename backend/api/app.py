from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    try:
        from .routes import api_bp
    except ImportError:
        from routes import api_bp

    app.register_blueprint(api_bp)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

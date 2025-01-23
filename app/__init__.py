from flask import Flask
from .routes import routes_bp

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # Registrar blueprint do app principal
    app.register_blueprint(routes_bp)
    
    return app

app = create_app()
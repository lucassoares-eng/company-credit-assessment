from flask import Blueprint

# Configure o Blueprint para usar uma pasta de templates específica
routes_bp = Blueprint(
    "credit_analysis",
    __name__,
    template_folder="templates",  # Caminho relativo para a pasta de templates do módulo
    static_folder="static",        # Caminho relativo para a pasta de arquivos estáticos do módulo
)
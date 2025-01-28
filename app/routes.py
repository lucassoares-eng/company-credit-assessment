from flask import Blueprint, redirect, render_template, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from .service import fetch_cnpj_data, fetch_company_data, fetch_facebook_followers, fetch_government_contracts, fetch_instagram_followers, fetch_reputation, pesquisaprotesto_search_protests

# Configure Blueprint to use a specific templates folder
routes_bp = Blueprint(
    "credit_analysis",
    __name__,
    template_folder="templates",  # Relative path to the module's templates folder
    static_folder="static",        # Relative path to the module's static files folder
)

# Setup Swagger UI
SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.json'  # Assuming openapi.json is located in the static folder

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Company Credit Assessment API"}
)

# Register Swagger UI Blueprint
routes_bp.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# Route to display a welcome message and redirect to Swagger UI
@routes_bp.route('/', methods=['GET'])
def home():
    # Redirect to the Swagger UI
    return redirect(SWAGGER_URL)

# Route to display CNPJ information
@routes_bp.route('/cnpj', methods=['GET'])
def cnpj_data():
    cnpj = request.args.get('cnpj')
    if cnpj:
        data = fetch_company_data(cnpj)
        return render_template('cnpj_data.html', data=data)
    return jsonify({'error': 'CNPJ parameter is required'}), 400

# Route to fetch the reputation of a company on Reclame Aqui
@routes_bp.route('/reputation', methods=['GET'])
def reputation():
    company_name = request.args.get('company_name')
    if company_name:
        rating = fetch_reputation(company_name)
        return jsonify({'company_name': company_name, 'rating': rating})
    return jsonify({'error': 'Company name parameter is required'}), 400

# Route to check protests for a company using its CNPJ
@routes_bp.route('/protests', methods=['GET'])
def protests():
    cnpj = request.args.get('cnpj')
    if cnpj:
        protest_info = pesquisaprotesto_search_protests(cnpj)
        return jsonify(protest_info)
    return jsonify({'error': 'CNPJ parameter is required'}), 400

# Route to fetch Instagram followers of a company
@routes_bp.route('/instagram-followers', methods=['GET'])
def instagram_followers():
    company_name = request.args.get('company_name')
    if company_name:
        url, followers = fetch_instagram_followers(company_name)
        return jsonify({'company_name': company_name, 'instagram_url': url, 'followers': followers})
    return jsonify({'error': 'Company name parameter is required'}), 400

# Route to fetch Facebook followers of a company
@routes_bp.route('/facebook-followers', methods=['GET'])
def facebook_followers():
    company_name = request.args.get('company_name')
    if company_name:
        url, followers = fetch_facebook_followers(company_name)
        return jsonify({'company_name': company_name, 'facebook_url': url, 'followers': followers})
    return jsonify({'error': 'Company name parameter is required'}), 400

# Route to fetch government contracts of a company by its CNPJ
@routes_bp.route('/government-contracts', methods=['GET'])
def government_contracts():
    cnpj = request.args.get('cnpj')
    if cnpj:
        has_contracts = fetch_government_contracts(cnpj)
        return jsonify({'cnpj': cnpj, 'has_government_contracts': has_contracts})
    return jsonify({'error': 'CNPJ parameter is required'}), 400

# Route to fetch detailed CNPJ data
@routes_bp.route('/cnpj-data', methods=['GET'])
def cnpj_data_route():
    cnpj = request.args.get('cnpj')
    if cnpj:
        cnpj_data = fetch_cnpj_data(cnpj)
        return jsonify(cnpj_data)
    return jsonify({'error': 'CNPJ parameter is required'}), 400

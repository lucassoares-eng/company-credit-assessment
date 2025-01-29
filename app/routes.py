from flask import Blueprint, redirect, render_template, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from .service import (
    fetch_cnpj_data,
    fetch_company_data,
    fetch_facebook_followers,
    fetch_government_contracts,
    fetch_instagram_followers,
    fetch_reputation,
    pesquisaprotesto_search_protests,
)
import requests

# Configure Blueprint to use a specific templates folder
routes_bp = Blueprint(
    "credit_analysis",
    __name__,
    template_folder="templates",  # Relative path to the module's templates folder
    static_folder="static",  # Relative path to the module's static files folder
)

# Setup Swagger UI
SWAGGER_URL = "/swagger"
API_URL = "/static/openapi.json"  # Assuming openapi.json is located in the static folder

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Company Credit Assessment API"}
)

# Register Swagger UI Blueprint
routes_bp.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# Route to display a welcome message and redirect to Swagger UI
@routes_bp.route("/", methods=["GET"])
def home():
    # Redirect to the Swagger UI
    return redirect(SWAGGER_URL)

# Route to display CNPJ information
@routes_bp.route("/company-data", methods=["GET"])
def cnpj_data():
    cnpj = request.args.get("cnpj")
    if not cnpj:
        return jsonify({"error": "CNPJ parameter is required"}), 400

    try:
        data = fetch_company_data(cnpj)
        if "error" in data:
            return jsonify({"error": data["error"]}), 404
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to fetch the reputation of a company on Reclame Aqui
@routes_bp.route("/reputation", methods=["GET"])
def reputation():
    company_name = request.args.get("company_name")
    if not company_name:
        return jsonify({"error": "Company name parameter is required"}), 400

    try:
        rating = fetch_reputation(company_name)
        if rating == 0:
            return jsonify({"error": "Company not found on Reclame Aqui"}), 404
        return jsonify({"company_name": company_name, "rating": rating})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to check protests for a company using its CNPJ
@routes_bp.route("/protests", methods=["GET"])
def protests():
    cnpj = request.args.get("cnpj")
    if not cnpj:
        return jsonify({"error": "CNPJ parameter is required"}), 400

    try:
        protest_info = pesquisaprotesto_search_protests(cnpj)
        if protest_info is None:
            return jsonify({"error": "No protests found for the given CNPJ"}), 404
        
        # Unpack the results from the function
        total_protests, total_protested_value = protest_info
        
        # Return the response in the desired format
        return jsonify({
            "cnpj": cnpj,
            "total_protests": total_protests,
            "total_protested_value": total_protested_value
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to fetch Instagram followers of a company
@routes_bp.route("/instagram-followers", methods=["GET"])
def instagram_followers():
    company_name = request.args.get("company_name")
    if not company_name:
        return jsonify({"error": "Company name parameter is required"}), 400

    try:
        url, followers = fetch_instagram_followers(company_name)
        if followers is None:
            return jsonify({"error": "Company Instagram page not found"}), 404
        return jsonify({"company_name": company_name, "instagram_url": url, "followers": followers})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to fetch Facebook followers of a company
@routes_bp.route("/facebook-followers", methods=["GET"])
def facebook_followers():
    company_name = request.args.get("company_name")
    if not company_name:
        return jsonify({"error": "Company name parameter is required"}), 400

    try:
        url, followers = fetch_facebook_followers(company_name)
        if followers is None:
            return jsonify({"error": "Company Facebook page not found"}), 404
        return jsonify({"company_name": company_name, "facebook_url": url, "followers": followers})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to fetch government contracts of a company by its CNPJ
@routes_bp.route("/government-contracts", methods=["GET"])
def government_contracts():
    cnpj = request.args.get("cnpj")
    if not cnpj:
        return jsonify({"error": "CNPJ parameter is required"}), 400

    try:
        has_contracts = fetch_government_contracts(cnpj)
        return jsonify({"cnpj": cnpj, "has_government_contracts": has_contracts})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route to fetch detailed CNPJ data
@routes_bp.route("/cnpj-data", methods=["GET"])
def cnpj_data_route():
    cnpj = request.args.get("cnpj")
    if not cnpj:
        return jsonify({"error": "CNPJ parameter is required"}), 400

    try:
        cnpj_data = fetch_cnpj_data(cnpj)
        if "error" in cnpj_data:
            return jsonify({"error": cnpj_data["error"]}), 404
        return jsonify(cnpj_data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"External service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
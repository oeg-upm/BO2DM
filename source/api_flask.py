import flask
from flask import request, jsonify
import sqlite3
from converter import o2dm_conversion
from flask_swagger_ui import get_swaggerui_blueprint

app = flask.Flask(__name__)
app.config["DEBUG"] = True


# swagger specific
swagger_url = "/swagger"
api_url = "/static/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    swagger_url,
    api_url,
    config={
        "app_name": "BO2DM Flask API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)

domains_available = {
    "occupancy_profile": {"prefix": "op", "name": "Occupancy Profile"},
    "key_performance_indicator": {"prefix": "kpi", "name": "Key Performance Indicator"},
    "weather_data": {"prefix": "weather", "name": "Weather Data"},
    "sensor_data": {"prefix": "sd", "name": "Sensor Data"}
}


@app.route("/", methods=["GET"])
def home():
    return "<h1>BIMERR Ontology to Data Model (BO2DM)</h1>" \
           "<p>Demo API for the ontology to data model " \
           "converter to be used by BIMERR project.</p>"

@app.route("/parameters", methods=["GET"])
def return_domains():

    return jsonify(domains_available)

@app.route("/domains", methods=["GET"])
def converter():
    query_parameters = request.args
    domain = query_parameters.get("domain")
    prefix = domains_available[domain]["prefix"]
    ontology_path = "ontology/" + prefix + "_enriched.ttl"
    data_model = o2dm_conversion(ontology_path)

    return jsonify(data_model)

if __name__ == "__main__":
    app.run()
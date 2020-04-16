import flask
from flask import request, jsonify
import sqlite3
from converter import o2dm_conversion

app = flask.Flask(__name__)
app.config["DEBUG"] = True

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

    message = ""
    for key, value in domains_available.items():
        message = message + "<p><b>" + value["name"] + ":</b>" + "&ensp;" + key + "</p>"
    return "<h1>Domains Available for Conversion</h1>" + message

@app.route("/domains", methods=["GET"])
def converter():
    query_parameters = request.args
    domain = query_parameters.get("domain")
    prefix = domains_available[domain]["prefix"]
    ontology_path = "ontology/" + prefix + "_enriched.ttl"
    data_model = o2dm_conversion(ontology_path)

    return jsonify(data_model)

app.run()
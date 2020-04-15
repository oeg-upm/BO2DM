import flask
from flask import request, jsonify
import sqlite3
from converter import o2dm_conversion

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route("/", methods=["GET"])
def home():
    return "<h1>BIMERR Ontology to Data Model (BO2DM)<h1>" \
           "<p>Demo API for the ontology to data model" \
           "converter to be used by BIMERR project.</p>"

@app.route("/", methods=["GET"])
def converter():
    query_parameters = request.args

    ont_uri = query_parameters.get("uri")
    data_model = o2dm_conversion(ont_uri)

    return jsonify(data_model)
import rdflib
from rdflib.serializer import Serializer
import json


def get_ontology_dict():

    ontos = {"building": "http://bimerr.iot.linkeddata.es/def/building#",
             "op": "http://bimerr.iot.linkeddata.es/def/occupancy-profile#",
             "sd": "http://bimerr.iot.linkeddata.es/def/sensor-data#",
             "bm": "http://bimerr.iot.linkeddata.es/def/metadata#",
             "mat": "http://bimerr.iot.linkeddata.es/def/material-properties#",
             "kpi": "http://bimerr.iot.linkeddata.es/def/key-performance-indicator#",
             "ao": "http://bimerr.iot.linkeddata.es/def/annotation-objects#",
             "io": "http://bimerr.iot.linkeddata.es/def/information-objects#",
             "renp": "http://bimerr.iot.linkeddata.es/def/renovation-process#"}

    return ontos

def load_ontology(ontology_path):

    """
    Function to load the ontology from the path provided as input, the output is the ontology
    implementation in a JSON-LD format. Also, as a side output, a dictionary with the namespaces used in the
    ontology is returned.

    :arg ontology_path: the absolute path to the ontology file in ttl format
    :returns jsonld_model: the ontology in a json-ld format
    :returns uri2prefix: dictionary with the namespaces used in the ontology. It has the following structure:
                        {"namespace_uri_1": ns_prefix_1, "namespace_uri_2": ns_prefix_2, ...}

    """

    g = rdflib.Graph()
    g.parse(ontology_path, format='ttl')
    namespaces = list(g.namespaces())
    uri2prefix = {str(uri): prefix for (prefix, uri) in namespaces}
    jsonld_model = g.serialize(format='json-ld', indent=4).decode()
    jsonld_model = json.loads(jsonld_model)

    return jsonld_model, uri2prefix


def get_annotation_property_uris():

    """
    Maps metadata URIs to the actual names used in the json data model
    :return:
            prefixes: dictionary with useful predefined prefixes, such as "owl" or "rdfs". The structure
                    of the dictionary is: {"prefix_1": "namespace_uri_1", "prefix_2": "namespace_uri_2", ...}

            annotations: dictionary with the mapping between the terms used in the data model and the
                    uris of the annotations used in the ontology. The structure is:
                    {"datamodel_term1": uri_ann_property1, "datamodel_term2": uri_ann_property2, ...}
    """

    annotations = {}
    prefixes = {}

    prefixes["rdfs"] = "http://www.w3.org/2000/01/rdf-schema#"
    prefixes["rdf"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    prefixes["dc"] = "http://purl.org/dc/elements/1.1/"
    prefixes["owl"] = "http://www.w3.org/2002/07/owl#"
    prefixes["skos"] = "http://www.w3.org/2004/02/skos/core#"
    prefixes["metadata"] = "http://bimerr.iot.linkeddata.es/def/bimerr-metadata#"

    annotations["definition"] = prefixes["rdfs"] + "comment"
    annotations["related_terms"] = prefixes["skos"] + "altLabel"
    annotations["standard"] = prefixes["metadata"] + "isDefinedByStandard"
    annotations["date_added"] = prefixes["dc"] + "created"
    annotations["date_deprecated"] = prefixes["metadata"] + "deprecated"
    annotations["version"] = prefixes["owl"] + "versionInfo"
    annotations["ordered"] = prefixes["metadata"] + "ordered"
    annotations["sensitive"] = prefixes["metadata"] + "sensitive"
    annotations["transformation"] = prefixes["metadata"] + "transformation"
    annotations["measurementType"] = prefixes["metadata"] + "measurementType"
    annotations["measurementUnit"] = prefixes["metadata"] + "measurementUnit"
    annotations["timeZone"] = prefixes["metadata"] + "timeZone"
    annotations["codeList"] = prefixes["metadata"] + "codeList"
    annotations["codeType"] = prefixes["metadata"] + "codeType"
    annotations["avoidElement"] = prefixes["metadata"] + "avoidElement"

    return annotations, prefixes

def get_element_name(element_uri):

    if "#" in element_uri:
        element_name = element_uri.split("#")[-1]
    else:
        element_name = element_uri.split("/")[-1]

    return element_name


def get_superclasses(element, prefixes):

    if prefixes["rdfs"] + "subClassOf" in element:
        superclasses = element[prefixes["rdfs"] + "subClassOf"]

    elif prefixes["owl"] + "NamedIndividual" in element["@type"]:
        for item in element["@type"]:
            if item != prefixes["owl"] + "NamedIndividual":
                superclasses = [{"@id": item}]

    else:
        superclasses = []

    return superclasses
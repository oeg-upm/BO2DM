import rdflib
from rdflib.serializer import Serializer
import json
import os

def find_ontology_element(element_uri, ont_jsonld):

    for element in ont_jsonld:
        if element["@id"] == element_uri:
            break
    return element

def get_classes(ont_jsonld):

    """Function to find all the classes inside an jsonld owl serialization."""

    total_concepts = []
    for element in ont_jsonld:
        try:
            # Classes have only one element inside the list "@type"
            type_uri = element["@type"][0]
            type = type_uri[type_uri.find("#") + 1:]
            if type == "Class" and element["@id"][0] != "_":
                total_concepts.append(element["@id"])
        except:
            continue
    return total_concepts

# Load ontology
ontology_path = "D:/oeg-projects/bimerr/BO2DM/ontology/test.ttl"
g = rdflib.Graph()
g.parse(ontology_path, format='ttl')
ont_jsonld = g.serialize(format='json-ld', indent=4).decode()
ont_jsonld = json.loads(ont_jsonld)
print(ont_jsonld)
data_model = {}

# Namespaces
building = "https://bimerr.iot.linkeddata.es/def/building#"
ont_uri = "https://bimerr.iot.linkeddata.es/def/occupancy-profile#"
rdfs = "http://www.w3.org/2000/01/rdf-schema#"
rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
dc = "http://purl.org/dc/elements/1.1/"
dcterms = "http://purl.org/dc/terms/"
owl = "http://www.w3.org/2002/07/owl#"
xsd = "http://www.w3.org/2001/XMLSchema"

concepts = get_classes(ont_jsonld)

for concept_uri in concepts:

    concept_name = concept_uri[concept_uri.find("#")+1:]
    element = find_ontology_element(concept_uri, ont_jsonld)
    definition = element[rdfs + "comment"][0]["@value"]
    standard = element[rdfs + "isDefinedBy"][0]["@value"]
    date_added = element[dc + "dateAdded"][0]["@value"]
    date_deprecated = element[dc + "dateDeprecated"][0]["@value"]
    version = element[dc + "version"][0]["@value"]
    data_model[concept_name] = {"definition": definition}
    data_model[concept_name]["standards"] = [standard]
    data_model[concept_name]["date_added"] = date_added
    data_model[concept_name]["date_deprecated"] = date_deprecated
    data_model[concept_name]["version"] = version
    superclasses = element[rdfs + "subClassOf"]
    data_model[concept_name]["children"] = {}

    for superclass in superclasses:
        superclass_uri = superclass["@id"]
        superclass_name = superclass_uri[superclass_uri.find("#") + 1:]
        superclass_element = find_ontology_element(superclass_uri, ont_jsonld)
        superclass_type = superclass_element["@type"][0]
        superclass_type_name = superclass_type[superclass_type.find("#") + 1:]

        if superclass_type_name != "Restriction":
            continue

        property_uri = superclass_element[owl + "onProperty"][0]["@id"]
        property_element = find_ontology_element(property_uri, ont_jsonld)
        property_types = property_element["@type"]

        # One property could be of more than one type
        #interesting_types = [owl+"ObjectProperty", owl+"DatatypeProperty"]
        #property_type = [type for type in property_types if type in interesting_types][0]

        #if property_type == owl + "ObjectProperty":
        if owl+"ObjectProperty" in property_types:
            try:
                range_uri = superclass_element[owl + "someValuesFrom"][0]["@id"]
            except:
                range_uri = superclass_element[owl + "allValuesFrom"][0]["@id"]

            range_name = range_uri[range_uri.find("#") + 1:]
            data_model[concept_name]["children"][range_name] = {"type": {"$ref": "#/" + range_name}}

            if owl + "FunctionalProperty" in property_types:
                data_model[concept_name]["children"][range_name]["facet"] = {"cardinalityMax": 1}
            else:
                max_cardinality = superclass_element[owl + "maxQualifiedCardinality"][0]["@value"]
                data_model[concept_name]["children"][range_name]["facet"] = {"cardinalityMax": max_cardinality}

        else:
            property_name = property_uri[property_uri.find("#") + 1:]
            data_model[concept_name]["children"][property_name] = {}
            definition = property_element[rdfs + "comment"][0]["@value"]
            standard = property_element[rdfs + "isDefinedBy"][0]["@value"]
            date_added = property_element[dc + "dateAdded"][0]["@value"]
            date_deprecated = property_element[dc + "dateDeprecated"][0]["@value"]
            version = property_element[dc + "version"][0]["@value"]
            ordered = property_element[dc + "ordered"][0]["@value"]
            sensitive = property_element[dc + "sensitive"][0]["@value"]
            data_model[concept_name]["children"][property_name]["definition"] = definition
            data_model[concept_name]["children"][property_name]["standards"] = [standard]
            data_model[concept_name]["children"][property_name]["date_added"] = date_added
            data_model[concept_name]["children"][property_name]["date-deprecated"] = date_deprecated
            data_model[concept_name]["children"][property_name]["version"] = version

            try:
                datatype = superclass_element[owl + "someValuesFrom"][0]["@id"]
            except:
                datatype = superclass_element[owl + "allValuesFrom"][0]["@id"]

            datatype = datatype[datatype.find("#") + 1:]
            data_model[concept_name]["children"][property_name]["type"] = datatype

            if owl + "FunctionalProperty" in property_types:
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": 1}
            else:
                max_cardinality = superclass_element[owl + "maxQualifiedCardinality"][0]["@value"]
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}

for i in data_model:
    print(i, data_model[i])


result = json.dumps(data_model, indent=4, separators=(',', ': '))

"""
with open("./op_data_model2.json", "w") as f:
    json.dump(ont_dict, f, indent=4, separators=(',', ': '))
"""

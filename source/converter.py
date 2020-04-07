import rdflib
from rdflib.serializer import Serializer
import json
import os

project_dir = os.path.dirname(os.getcwd())

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

def enrich_model(ont_jsonld, metadata):

    for meta_element in metadata:
        # This condition try except is because of the fact that there could exist some standards
        # defined as a Literal or with a URI pointing to their HTML documentation.
        try:
            standard = meta_element[rdfs + "isDefinedBy"][0]["@value"] if rdfs + "isDefinedBy" in meta_element else None
        except:
            standard = meta_element[rdfs + "isDefinedBy"][0]["@id"] if rdfs + "isDefinedBy" in meta_element else None
        date_added = meta_element[dc + "dateAdded"][0]["@value"] if dc + "dateAdded" in meta_element else None
        date_deprecated = meta_element[dc + "dateDeprecated"][0]["@value"] if dc + "dateDeprecated" in meta_element else None
        version = meta_element[owl + "versionInfo"][0]["@value"] if owl + "versionInfo" in meta_element else None

        for ont_element in ont_jsonld:
            if meta_element["@id"] == ont_element["@id"]:

                ont_element[rdfs+"isDefinedBy"] = [{"@value": standard}]
                ont_element[dc+"dateAdded"] = [{"@value": date_added}]
                ont_element[dc+"dateDeprecated"] = [{"@value": date_deprecated}]
                ont_element[owl+"versionInfo"] = [{"@value": version}]
                break

    return ont_jsonld

# Load ontology
metadata_path = "D:/oeg-projects/bimerr/BO2DM/ontology/op_enriched.ttl"
g1 = rdflib.Graph()
g1.parse(metadata_path, format='ttl')
metadata_jsonld = g1.serialize(format='json-ld', indent=4).decode()
metadata_jsonld = json.loads(metadata_jsonld)

for element in metadata_jsonld:
    print(element)
data_model = {}

# Namespaces
rdfs = "http://www.w3.org/2000/01/rdf-schema#"
rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
dc = "http://purl.org/dc/elements/1.1/"
dcterms = "http://purl.org/dc/terms/"
owl = "http://www.w3.org/2002/07/owl#"
xsd = "http://www.w3.org/2001/XMLSchema"

for element in metadata_jsonld:
    if owl+"imports" in element:
        imported_ont = element[owl+"imports"][0]["@id"]
        break

g2 = rdflib.Graph()
g2.parse(imported_ont[:-1]+"/ontology.ttl", format='ttl')
ont_jsonld = g2.serialize(format='json-ld', indent=4).decode()
ont_jsonld = json.loads(ont_jsonld)

ont_enriched_jsonld = enrich_model(ont_jsonld, metadata_jsonld)

concepts = get_classes(ont_enriched_jsonld)

for concept_uri in concepts:

    concept_name = concept_uri[concept_uri.find("#")+1:]
    element = find_ontology_element(concept_uri, ont_enriched_jsonld)
    definition = element[rdfs+"comment"][0]["@value"] if rdfs+"comment" in element else None
    # This condition try except is because of the fact that there could exist some standards
    # defined as a Literal or with a URI pointing to their HTML documentation.
    try:
        standard = element[rdfs+"isDefinedBy"][0]["@value"] if rdfs+"isDefinedBy" in element else None
    except:
        standard = element[rdfs+"isDefinedBy"][0]["@id"] if rdfs+"isDefinedBy" in element else None
    date_added = element[dc+"dateAdded"][0]["@value"] if dc+"dateAdded" in element else None
    date_deprecated = element[dc+"dateDeprecated"][0]["@value"] if dc+"dateDeprecated" in element else None
    version = element[owl+"versionInfo"][0]["@value"] if owl+"versionInfo" in element else None
    data_model[concept_name] = {"definition": definition}
    data_model[concept_name]["standards"] = [standard]
    data_model[concept_name]["date_added"] = date_added
    data_model[concept_name]["date_deprecated"] = date_deprecated
    data_model[concept_name]["version"] = version
    superclasses = element[rdfs+"subClassOf"] if rdfs+"subClassOf" in element else []
    data_model[concept_name]["children"] = {}

    for superclass in superclasses:
        superclass_uri = superclass["@id"]
        superclass_name = superclass_uri[superclass_uri.find("#") + 1:]
        superclass_element = find_ontology_element(superclass_uri, ont_enriched_jsonld)
        superclass_type = superclass_element["@type"][0]
        superclass_type_name = superclass_type[superclass_type.find("#") + 1:]

        if superclass_type_name != "Restriction":
            continue

        property_uri = superclass_element[owl + "onProperty"][0]["@id"]
        property_element = find_ontology_element(property_uri, ont_enriched_jsonld)
        property_types = property_element["@type"]
        property_name = property_uri[property_uri.find("#") + 1:]

        data_model[concept_name]["children"][property_name] = {}
        definition = property_element[rdfs + "comment"][0]["@value"] if rdfs + "comment" in property_element else None
        try:
            standard = property_element[rdfs + "isDefinedBy"][0]["@value"] if rdfs + "isDefinedBy" in property_element else None
        except:
            standard = property_element[rdfs+"isDefinedBy"][0]["@id"] if rdfs+"isDefinedBy" in property_element else None
        date_added = property_element[dc + "dateAdded"][0]["@value"] if dc + "dateAdded" in property_element else None
        date_deprecated = property_element[dc + "dateDeprecated"][0][
            "@value"] if dc + "dateDeprecated" in property_element else None
        version = property_element[owl + "versionInfo"][0][
            "@value"] if owl + "versionInfo" in property_element else None
        ordered = property_element[dc + "ordered"][0]["@value"] if dc + "ordered" in property_element else None
        sensitive = property_element[dc + "sensitive"][0]["@value"] if dc + "sensitive" in property_element else None
        data_model[concept_name]["children"][property_name]["definition"] = definition
        data_model[concept_name]["children"][property_name]["standards"] = [standard]
        data_model[concept_name]["children"][property_name]["date_added"] = date_added
        data_model[concept_name]["children"][property_name]["date_deprecated"] = date_deprecated
        data_model[concept_name]["children"][property_name]["version"] = version

        if owl + "someValuesFrom" in superclass_element:
            datatype = superclass_element[owl + "someValuesFrom"][0]["@id"]
        elif owl + "allValuesFrom" in superclass_element:
            datatype = superclass_element[owl + "allValuesFrom"][0]["@id"]
        else:
            datatype = superclass_element[owl + "onClass"][0]["@id"]

        datatype = datatype[datatype.find("#") + 1:]

        if owl + "FunctionalProperty" in property_types:
            data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": 1}
        elif owl + "maxQualifiedCardinality" in superclass_element:
            max_cardinality = superclass_element[owl + "maxQualifiedCardinality"][0]["@value"]
            data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}
        else:
            data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": None}

        data_model[concept_name]["children"][property_name]["facet"]["ordered"] = ordered
        data_model[concept_name]["children"][property_name]["facet"]["sensitive"] = sensitive

        if owl+"ObjectProperty" in property_types:
            data_model[concept_name]["children"][property_name]["type"] = {"$ref": "#/" + datatype}
        else:
            data_model[concept_name]["children"][property_name]["type"] = datatype

for concept_uri in concepts:

    concept_name = concept_uri[concept_uri.find("#")+1:]
    element = find_ontology_element(concept_uri, ont_enriched_jsonld)
    superclasses = element[rdfs + "subClassOf"] if rdfs + "subClassOf" in element else []

    for superclass in superclasses:
        superclass_uri = superclass["@id"]
        superclass_name = superclass_uri[superclass_uri.find("#") + 1:]
        superclass_element = find_ontology_element(superclass_uri, ont_enriched_jsonld)
        superclass_type = superclass_element["@type"][0]
        superclass_type_name = superclass_type[superclass_type.find("#") + 1:]

        if superclass_type_name != "Class":
            continue

        superclass_children = data_model[superclass_name]["children"]

        for key, element in superclass_children.items():
            data_model[concept_name]["children"][key] = element

#for i in data_model:
#    print(i, data_model[i])

result = json.dumps(data_model, indent=4, separators=(',', ': '))

with open(project_dir + "/output/op_data_model.json", "w") as f:
    json.dump(data_model, f, indent=4, separators=(',', ': '))


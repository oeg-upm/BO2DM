import rdflib
from rdflib.serializer import Serializer
import json
import argparse
import re

from modules.utils import *
from modules.finding import *
from modules.populating import *


def o2dm_conversion(ontology_path, output_datamodel_path=None):

    ontology_prefix = ontology_path.split("/")[-1].split("_")[0]
    enriched_onto, _ = load_ontology(ontology_path)
    data_model = {}
    ann_uris, prefixes = get_annotation_property_uris()
    all_ontologies = get_ontology_dict()
    ontology_uri = all_ontologies[ontology_prefix]

    for element in enriched_onto:
        if prefixes["owl"] + "imports" in element:
            imported_ontos = element[prefixes["owl"] + "imports"]
            imported_ontos = [onto["@id"] for onto in imported_ontos if ontology_uri in onto["@id"]]
            original_onto_uri = imported_ontos[0]
            break

    original_onto, ns2prefix = load_ontology(original_onto_uri[:-1]+"/ontology.ttl")
    enriched_onto = enrich_model(original_onto, enriched_onto)
    concepts, relations, attributes, individuals = get_all_uris(enriched_onto)
    concepts = concepts + individuals

    # Children identification evaluating Restrictions
    for concept_uri in concepts:
        if "#" in concept_uri:
            concept_ns = concept_uri.split("#")[0]
            concept_name = concept_uri.split("#")[1]
        else:
            concept_name = concept_uri.split("/")[-1]
            concept_ns = concept_uri.split(concept_name)[0][:-1]
        element = find_ontology_element(concept_uri, enriched_onto)

        concept_metadata = extract_elem_metadata(element)
        # This if else condition deals with strange cases when two concepts have the same name
        # like bot:Space and building:Space, in this case we just take the metadata from the most
        # specific concept.
        if concept_name in data_model:
            if concept_ns == original_onto:
                populate_datamodel_elements(data_model[concept_name], concept_metadata)
        else:
            data_model[concept_name] = {}
            populate_datamodel_elements(data_model[concept_name], concept_metadata)
            data_model[concept_name]["children"] = {}

        if prefixes["rdfs"] + "subClassOf" in element:
            superclasses = element[prefixes["rdfs"] + "subClassOf"]
        elif prefixes["owl"] + "NamedIndividual" in element["@type"]:
            for item in element["@type"]:
                if item != prefixes["owl"] + "NamedIndividual":
                    superclasses = [{"@id": item}]
        else:
            superclasses = []

        for superclass in superclasses:
            superclass_uri = superclass["@id"]
            superclass_element = find_ontology_element(superclass_uri, enriched_onto)
            superclass_type = superclass_element["@type"][0].split("#")[-1]

            if superclass_type != "Restriction":
                continue

            property_uri = superclass_element[prefixes["owl"] + "onProperty"][0]["@id"]
            property_element = find_ontology_element(property_uri, enriched_onto)
            property_types = property_element["@type"]

            if "#" in property_uri:
                property_name = property_uri.split("#")[-1]
            else:
                property_name = property_uri.split("/")[-1]

            if prefixes["rdfs"] + "range" in property_element:
                property_range = property_element[prefixes["rdfs"] + "range"]
            else:
                property_range = None

            property_metadata = extract_elem_metadata(property_element)
            data_model[concept_name]["children"][property_name] = {}
            populate_datamodel_elements(data_model[concept_name]["children"][property_name], property_metadata)

            datatype = None

            # To determine the datatype of a property, first check the existence of a restriction
            if prefixes["owl"] + "someValuesFrom" in superclass_element:
                datatype = superclass_element[prefixes["owl"] + "someValuesFrom"][0]["@id"]
                datatype = extract_datatype(datatype, prefixes, enriched_onto)

            elif prefixes["owl"] + "allValuesFrom" in superclass_element:
                datatype = superclass_element[prefixes["owl"] + "allValuesFrom"][0]["@id"]
                datatype = extract_datatype(datatype, prefixes, enriched_onto)

            elif prefixes["owl"] + "onClass" in superclass_element:
                datatype = superclass_element[prefixes["owl"] + "onClass"][0]["@id"]

                if "#" in datatype:
                    datatype = datatype.split("#")[-1]
                else:
                    datatype = datatype.split("/")[-1]

            # If there is not a restriction of type "some", "all" or "cardinality" check the range
            # I'm considering properly evaluated models, range dataype == restriction datatypes
            if property_range is not None:
                if "#" in property_range[0]["@id"]:
                    datatype = property_range[0]["@id"].split("#")[-1]
                else:
                    datatype = property_range[0]["@id"].split("/")[-1]

            if prefixes["owl"] + "FunctionalProperty" in property_types:
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": 1}
            elif prefixes["owl"] + "maxQualifiedCardinality" in superclass_element:
                max_cardinality = superclass_element[prefixes["owl"] + "maxQualifiedCardinality"][0]["@value"]
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}
            elif prefixes["owl"] + "qualifiedCardinality" in superclass_element:
                max_cardinality = superclass_element[prefixes["owl"] + "qualifiedCardinality"][0]["@value"]
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}
            elif prefixes["owl"] + "maxCardinality" in superclass_element:
                max_cardinality = superclass_element[prefixes["owl"] + "maxCardinality"][0]["@value"]
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}
            elif prefixes["owl"] + "cardinality" in superclass_element:
                max_cardinality = superclass_element[prefixes["owl"] + "cardinality"][0]["@value"]
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": max_cardinality}
            else:
                data_model[concept_name]["children"][property_name]["facet"] = {"cardinalityMax": None}

            populate_datamodel_elements(data_model[concept_name]["children"][property_name]["facet"],
                                        property_metadata, facet=True)

            if prefixes["owl"] + "ObjectProperty" in property_types:
                if type(datatype) == list:
                    datatype = ["#/" + item for item in datatype]
                    data_model[concept_name]["children"][property_name]["type"] = {"$ref": datatype}
                else:
                    data_model[concept_name]["children"][property_name]["type"] = {"$ref": "#/" + datatype}
            else:
                data_model[concept_name]["children"][property_name]["type"] = datatype

    # Children identification evaluating Domain and Range in Object Properties
    for relation_uri in relations:

        relation_element = find_ontology_element(relation_uri, enriched_onto)

        if prefixes["rdfs"] + "domain" in relation_element:
            property_domain = relation_element[prefixes["rdfs"] + "domain"][0]["@id"]

            if "#" in property_domain:
                domain_name = property_domain.split("#")[-1]
            else:
                domain_name = property_domain.split("/")[-1]

            if "#" in relation_uri:
                relation_name = relation_uri.split("#")[-1]
            else:
                relation_name = relation_uri.split("/")[-1]

            if relation_name not in data_model[domain_name]["children"]:
                relation_metadata = extract_elem_metadata(relation_element)
                data_model[domain_name]["children"][relation_name] = {}
                populate_datamodel_elements(data_model[domain_name]["children"][relation_name], relation_metadata)

                if prefixes["rdfs"] + "range" in relation_element:
                    relation_range = relation_element[prefixes["rdfs"] + "range"]
                else:
                    relation_range = None

                if relation_range is not None:
                    if "#" in relation_range[0]["@id"]:
                        datatype = relation_range[0]["@id"].split("#")[-1]
                    else:
                        datatype = relation_range[0]["@id"].split("/")[-1]

                    data_model[domain_name]["children"][relation_name]["type"] = {"$ref": "#/" + datatype}

    # Children identification evaluating Domain and Range in Datatype Properties
    for attribute_uri in attributes:

        attribute_element = find_ontology_element(attribute_uri, enriched_onto)

        if prefixes["rdfs"] + "domain" in attribute_element:
            property_domain = attribute_element[prefixes["rdfs"] + "domain"][0]["@id"]

            if "#" in property_domain:
                domain_name = property_domain.split("#")[-1]
            else:
                domain_name = property_domain.split("/")[-1]

            if "#" in attribute_uri:
                attribute_name = attribute_uri.split("#")[-1]
            else:
                attribute_name = attribute_uri.split("/")[-1]

            if attribute_name not in data_model[domain_name]["children"]:
                attribute_metadata = extract_elem_metadata(attribute_element)
                data_model[domain_name]["children"][attribute_name] = {}
                populate_datamodel_elements(data_model[domain_name]["children"][attribute_name], attribute_metadata)

                if prefixes["rdfs"] + "range" in attribute_element:
                    attribute_range = attribute_element[prefixes["rdfs"] + "range"]
                else:
                    attribute_range = None

                if attribute_range is not None:
                    if "#" in attribute_range[0]["@id"]:
                        datatype = attribute_range[0]["@id"].split("#")[-1]
                    else:
                        datatype = attribute_range[0]["@id"].split("/")[-1]

                    data_model[domain_name]["children"][attribute_name]["type"] = {"$ref": "#/" + datatype}

    # I do not foresee a taxonomy deeper than 4 levels
    for i in range(4):
        # Children identification evaluating SubClasses
        for concept_uri in concepts:

            if "#" in concept_uri:
                concept_name = concept_uri.split("#")[-1]
            else:
                concept_name = concept_uri.split("/")[-1]
            element = find_ontology_element(concept_uri, enriched_onto)
            
            if prefixes["rdfs"] + "subClassOf" in element:
                superclasses = element[prefixes["rdfs"] + "subClassOf"]
            elif prefixes["owl"] + "NamedIndividual" in element["@type"]:
                for item in element["@type"]:
                    if item != prefixes["owl"] + "NamedIndividual":
                        superclasses = [{"@id": item}]
            else:
                superclasses = []

            for superclass in superclasses:
                superclass_uri = superclass["@id"]
                if "#" in superclass_uri:
                    superclass_name = superclass_uri.split("#")[-1]
                else:
                    superclass_name = superclass_uri.split("/")[-1]

                if concept_name == superclass_name:
                    break

                superclass_element = find_ontology_element(superclass_uri, enriched_onto)
                superclass_type = superclass_element["@type"][0].split("#")[-1]

                if superclass_type != "Class":
                    continue

                superclass_children = data_model[superclass_name]["children"]

                if "hasSubClass" in superclass_children:
                    subclasses = data_model[superclass_name]["children"]["hasSubClass"]["type"]["$ref"]
                    if "#/" + concept_name not in subclasses:
                        data_model[superclass_name]["children"]["hasSubClass"]["type"]["$ref"].append("#/" + concept_name)
                else:
                    data_model[superclass_name]["children"]["hasSubClass"] = {"type": {"$ref": ["#/" + concept_name]}}

                for key, element in superclass_children.items():
                    if key == "hasSubClass":
                        continue
                    data_model[concept_name]["children"][key] = element

    if output_datamodel_path:
        with open(output_datamodel_path, "w") as f:
            json.dump(data_model, f, indent=4, separators=(',', ': '))

    return data_model


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Ontology to data model conversion")
    parser.add_argument("ontology_path", help="Full path to the ontology model")
    parser.add_argument("datamodel_output_path", help="Full path to the output data model")
    args = parser.parse_args()

    o2dm_conversion(args.ontology_path, args.datamodel_output_path)
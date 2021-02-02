import rdflib
from rdflib.serializer import Serializer
import json
import argparse
import re
import os

from modules.utils import *
from modules.finding import *
from modules.populating import *


def o2dm_conversion(ontology_path, output_datamodel_path=None, local_ontology_dir=None):

    ontology_prefix = ontology_path.split("/")[-1].split("_")[0]
    enriched_onto, _ = load_ontology(ontology_path)
    data_model = {}
    ann_uris, prefixes = get_annotation_property_uris()
    all_ontologies = get_ontology_dict()
    ontology_uri = all_ontologies[ontology_prefix]

    # Look for the original ontology in the "imports" section
    for element in enriched_onto:
        if prefixes["owl"] + "imports" in element:
            imported_ontos = element[prefixes["owl"] + "imports"]
            imported_ontos = [onto["@id"] for onto in imported_ontos if ontology_uri in onto["@id"]]
            original_onto_uri = imported_ontos[0]
            break
    
    if local_ontology_dir:
        ontology_filename = local_ontology_dir + "/" + ontology_prefix + ".ttl"
        print("Original Onto: ", ontology_filename)
        original_onto, _ = load_ontology(ontology_filename)
    else:
        original_onto, _ = load_ontology(original_onto_uri[:-1]+"/ontology.ttl")

    enriched_onto = enrich_model(original_onto, enriched_onto)
    concepts, relations, attributes, individuals = get_all_uris(enriched_onto)
    concepts = concepts + individuals
    properties = relations + attributes

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

        # Identify the superclasses of the Concept or Individual
        superclasses = get_superclasses(element, prefixes)

        for superclass in superclasses:
            superclass_uri = superclass["@id"]
            superclass_element = find_ontology_element(superclass_uri, enriched_onto)
            superclass_type = superclass_element["@type"][0].split("#")[-1]

            if superclass_type != "Restriction":
                continue

            property_uri = superclass_element[prefixes["owl"] + "onProperty"][0]["@id"]
            property_element = find_ontology_element(property_uri, enriched_onto)
            property_types = property_element["@type"]

            property_name = get_element_name(property_uri)
            property_name = re.sub("has", "", property_name)

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
                datatype = get_element_name(datatype)

            elif prefixes["owl"] + "onDataRange" in superclass_element:
                datatype = superclass_element[prefixes["owl"] + "onDataRange"][0]["@id"]
                datatype = get_element_name(datatype)

            # If there is not a restriction of type "some", "all" or "cardinality" check the range
            # I'm considering properly evaluated models, range dataype == restriction datatypes
            if property_range is not None:
                datatype = get_element_name(property_range[0]["@id"])

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


    # Children identification evaluating Domain and Range in Properties
    for property_uri in properties:

        property_element = find_ontology_element(property_uri, enriched_onto)

        if prefixes["rdfs"] + "domain" in property_element:
            property_domain = property_element[prefixes["rdfs"] + "domain"][0]["@id"]
            domain_name = get_element_name(property_domain)
            property_name = get_element_name(property_uri)
            property_name = re.sub("has", "", property_name)

            if property_name not in data_model[domain_name]["children"]:
                property_metadata = extract_elem_metadata(property_element)
                data_model[domain_name]["children"][property_name] = {}
                populate_datamodel_elements(data_model[domain_name]["children"][property_name], property_metadata)

                if prefixes["rdfs"] + "range" in property_element:
                    property_range = property_element[prefixes["rdfs"] + "range"]
                else:
                    property_range = None

                if property_range is not None:

                    datatype = get_element_name(property_range[0]["@id"])
                    data_model[domain_name]["children"][property_name]["type"] = {"$ref": "#/" + datatype}

    # I do not foresee a taxonomy deeper than 4 levels
    for i in range(4):
        # Children identification evaluating SubClasses
        for concept_uri in concepts:
            
            concept_name = get_element_name(concept_uri)
            element = find_ontology_element(concept_uri, enriched_onto)
            superclasses = get_superclasses(element, prefixes)

            for superclass in superclasses:
                superclass_uri = superclass["@id"]
                superclass_name = get_element_name(superclass_uri)

                if concept_name == superclass_name:
                    break

                superclass_element = find_ontology_element(superclass_uri, enriched_onto)
                superclass_type = superclass_element["@type"][0].split("#")[-1]

                if superclass_type != "Class":
                    continue

                superclass_children = data_model[superclass_name]["children"]
                data_model[concept_name]["children"]["parent"] = {"$ref": "#/" + superclass_name}
                for key, element in superclass_children.items():
                    if key == "parent":
                        continue
                    data_model[concept_name]["children"][key] = element


    if output_datamodel_path:
        with open(output_datamodel_path, "w") as f:
            json.dump(data_model, f, indent=4, separators=(',', ': '))

    return data_model


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Ontology to data model conversion")
    parser.add_argument("enriched_ontology_path", help="Full path to the ontology model enriched with metadata")
    parser.add_argument("datamodel_output_path", help="Full path to the output data model")
    parser.add_argument("-ontology_dir", help="Directory path to the original ontology")
    args = parser.parse_args()

    o2dm_conversion(args.enriched_ontology_path, args.datamodel_output_path, args.ontology_dir)
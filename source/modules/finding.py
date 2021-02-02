"""
Module with functions related to finding or extract specific information inside an ontology.
"""

from modules.utils import get_annotation_property_uris


def find_ontology_element(element_uri, ont_jsonld):
    """
    Function to return a specific ontology element within the model.

    :arg element_uri: Uri of the element we want to find
    :arg ont_jsonld: ontology in JSON-LD format
    :return: element: dictionary with the content of the desired element.
    """

    for element in ont_jsonld:
        if element["@id"] == element_uri:
            break
    return element


def get_all_uris(ont_jsonld):
    """
    Function to find all the uris of the concepts, relations, and attributes inside an ontology.

    :arg ont_jsonld: ontology serialized as JSON-LD
    :return: classes: Uris of all the classes inside an ontology
            relations: Uris of all the object properties inside an ontology
            attributes: Uris of all the datatype properties inside an ontology
    """

    classes = []
    relations = []
    attributes = []
    individuals = []

    for element in ont_jsonld:
        try:
            # Classes have only one element inside the list "@type"
            for single_type in element["@type"]:
                type_ = single_type.split("#")[-1]
                # The "_" comparison avoids the inclusion of blank nodes in the list
                if type_ == "Class" and element["@id"][0] != "_":
                    classes.append(element["@id"])
                    break
                elif type_ == "ObjectProperty":
                    relations.append(element["@id"])
                    break
                elif type_ == "DatatypeProperty":
                    attributes.append(element["@id"])
                    break
                elif type_ == "NamedIndividual":
                    individuals.append(element["@id"])
                    break
        except:
            continue

    return classes, relations, attributes, individuals


def extract_elem_metadata(enriched_element):
    """
    Extract the annotations made to an ontology element in the enriched model
    :arg ontology element from the enriched version of the model
    :return A dictionary containing the annotations made to the ontology element during the enrichment phase.
    """

    annotations_extracted = {}
    ann, _ = get_annotation_property_uris()

    for metadata_name in ann.keys():

        metadata_uri = ann[metadata_name]
        annotations_extracted[metadata_name] = enriched_element[metadata_uri][0]["@value"] if metadata_uri in enriched_element else None

    return annotations_extracted


def extract_datatype(datatype, prefixes, ont_jsonld):
    """
    Support function to find the correct class associated to an object property when
    the target of the property is a blank node like the case of a union or intersection axiom.
    """
    if "_:" in datatype:
        blank_node = find_ontology_element(datatype, ont_jsonld)
        if prefixes["owl"] + "unionOf" in blank_node:
            datatype = []
            ref_concepts = blank_node[prefixes["owl"] + "unionOf"][0]["@list"]
            for item in ref_concepts:
                if "#" in item["@id"]:
                    ref_concept_name = item["@id"].split("#")[-1]
                else:
                    ref_concept_name = item["@id"].split("/")[-1]
                datatype.append(ref_concept_name)

        elif prefixes["owl"] + "intersectionOf" in blank_node:
            datatype = []
            ref_concepts = blank_node[prefixes["owl"] + "intersectionOf"][0]["@list"]
            for item in ref_concepts:
                if "#" in item["@id"]:
                    ref_concept_name = item["@id"].split("#")[-1]
                else:
                    ref_concept_name = item["@id"].split("/")[-1]
                datatype.append(ref_concept_name)
    else:
        if "#" in datatype:
            datatype = datatype.split("#")[-1]
        else:
            datatype = datatype.split("/")[-1]

    return datatype
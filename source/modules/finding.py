"""
Module with functions related to finding or extract specific information inside an ontology.
"""

from modules.utils import get_annotation_property_uris


def find_ontology_element(element_uri, ont_jsonld):

    """
    Function to return all the information of an ontological element
    wheter it is a class, property or attribute.

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
            type = element["@type"][0].split("#")[-1]
            # The "_" comparison avoids the inclusion of blank nodes in the list
            if type == "Class" and element["@id"][0] != "_":
                classes.append(element["@id"])
            elif type == "ObjectProperty":
                relations.append(element["@id"])
            elif type == "DatatypeProperty":
                attributes.append(element["@id"])
            elif type == "NamedIndividual":
                individuals.append(element["@id"])
        except:
            continue

    return classes, relations, attributes, individuals


def extract_elem_metadata(element):

    """
    Extract all the annotations made to the element in the enriched model
    arg: element: ontological element in a dictionary form {element_uri: content},
                the user should assume that the ontology is in a JSON-LD format.
    return: annotations_extracted: a dictionary containing all the annotations of that element
                                during enrichment time. The strucure is:
                                {metada_term: value, ...}
    """

    ann, _ = get_annotation_property_uris()
    annotations_extracted = {}

    # Metadata extraction from the metadata ontology
    definition = element[ann["definition"]][0]["@value"] if ann["definition"] in element else None
    related_terms = element[ann["terms"]][0]["@value"] if ann["terms"] in element else None
    standard = element[ann["standard"]][0]["@value"] if ann["standard"] in element else None
    date_added = element[ann["added"]][0]["@value"] if ann["added"] in element else None
    date_deprecated = element[ann["deprecated"]][0]["@value"] if ann["deprecated"] in element else None
    version = element[ann["version"]][0]["@value"] if ann["version"] in element else None
    ordered = element[ann["ordered"]][0]["@value"] if ann["ordered"] in element else None
    sensitive = element[ann["sensitive"]][0]["@value"] if ann["sensitive"] in element else None
    transformation = element[ann["transformation"]][0]["@value"] if ann["transformation"] in element else None
    measurementType = element[ann["measureType"]][0]["@value"] if ann["measureType"] in element else None
    measurementUnit = element[ann["measureUnit"]][0]["@value"] if ann["measureUnit"] in element else None
    timeZone = element[ann["timeZone"]][0]["@value"] if ann["timeZone"] in element else None
    codeList = element[ann["codeList"]][0]["@value"] if ann["codeList"] in element else None
    codeType = element[ann["codeType"]][0]["@value"] if ann["codeType"] in element else None

    annotations_extracted["definition"] = definition
    annotations_extracted["related_terms"] = related_terms
    annotations_extracted["standard"] = standard
    annotations_extracted["date_added"] = date_added
    annotations_extracted["date_deprecated"] = date_deprecated
    annotations_extracted["version"] = version
    annotations_extracted["ordered"] = ordered
    annotations_extracted["sensitive"] = sensitive
    annotations_extracted["transformation"] = transformation
    annotations_extracted["measurementType"] = measurementType
    annotations_extracted["measurementUnit"] = measurementUnit
    annotations_extracted["timeZone"] = timeZone
    annotations_extracted["codeList"] = codeList
    annotations_extracted["codeType"] = codeType

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
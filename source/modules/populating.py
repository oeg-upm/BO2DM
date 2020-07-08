"""
Module with functions related to populating information inside a data structure.
"""

from modules.utils import get_annotation_property_uris
from modules.finding import extract_elem_metadata


def enrich_model(original_model, enriched_model):

    """
    Function to merge an ontology and the enriched version.
    The enriched model just contains these extra annotations.

    :param original_model: ontological model serialized as JSON-LD
    :param enriched_model: enriched ontological model serialized as JSON-LD
    :return: a unified ontological model with the original information from the domain and
            the extra annotations.
    """

    ann_uris, _ = get_annotation_property_uris()

    for meta_element in enriched_model:

        # Metadata extraction from the metadata ontology
        metadata_extracted = extract_elem_metadata(meta_element)

        # Metadata population on the original ontology
        for ont_element in original_model:
            if meta_element["@id"] == ont_element["@id"]:

                type = ont_element["@type"][0].split("#")[-1]

                ont_element[ann_uris["standard"]] = [{"@value": metadata_extracted["standard"]}]
                ont_element[ann_uris["terms"]] = [{"@value": metadata_extracted["related_terms"]}]
                ont_element[ann_uris["added"]] = [{"@value": metadata_extracted["date_added"]}]
                ont_element[ann_uris["deprecated"]] = [{"@value": metadata_extracted["date_deprecated"]}]
                ont_element[ann_uris["version"]] = [{"@value": metadata_extracted["version"]}]

                # The following metadata fields are only used by children elements
                if type != "Class":
                    ont_element[ann_uris["ordered"]] = [{"@value": metadata_extracted["ordered"]}]
                    ont_element[ann_uris["sensitive"]] = [{"@value": metadata_extracted["sensitive"]}]
                    ont_element[ann_uris["transformation"]] = [{"@value": metadata_extracted["transformation"]}]
                    ont_element[ann_uris["measureType"]] = [{"@value": metadata_extracted["measurementType"]}]
                    ont_element[ann_uris["measureUnit"]] = [{"@value": metadata_extracted["measurementUnit"]}]
                    ont_element[ann_uris["timeZone"]] = [{"@value": metadata_extracted["timeZone"]}]
                    ont_element[ann_uris["codeList"]] = [{"@value": metadata_extracted["codeList"]}]
                    ont_element[ann_uris["codeType"]] = [{"@value": metadata_extracted["codeType"]}]
                break

    return original_model


def populate_datamodel_elements(data_model_element, metadata, facet=False):

    """
    Populate the data model element with all the metadata needed

    :param data_model_element: dictionary with the data model element selected
    :param metadata: dictionary with all the metadata extracted from the ontology
    :param facet: boolean flag to indicate that the element is a children and require the
            population of extra annotations
    :return: dictionary with the data model element populated
    """

    if facet == False:
        data_model_element["definition"] = metadata["definition"]
        data_model_element["related_terms"] = [metadata["related_terms"]]
        data_model_element["standards"] = [metadata["standard"]]
        data_model_element["date_added"] = metadata["date_added"]
        data_model_element["date_deprecated"] = metadata["date_deprecated"]
        data_model_element["version"] = metadata["version"]

    else:
        data_model_element["ordered"] = metadata["ordered"]
        data_model_element["sensitive"] = metadata["sensitive"]
        data_model_element["transformation"] = metadata["transformation"]
        data_model_element["measurementType"] = metadata["measurementType"]
        data_model_element["measurementUnit"] = metadata["measurementUnit"]
        data_model_element["timeZone"] = metadata["timeZone"]
        data_model_element["codeList"] = metadata["codeList"]
        data_model_element["codeType"] = metadata["codeType"]

    return data_model_element

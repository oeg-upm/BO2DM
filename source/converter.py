import rdflib
from rdflib.serializer import Serializer
import json
import re


def find_ontology_element(element_id, ont_jsonld):
    for element in ont_jsonld:
        if element["@id"] == element_id:
            break
    return element


ontology = "C:/Users/HP/ownCloud/BIMMERR ownCloud/WP4/T4.2/Ontology converter/input_ontology.ttl"

g = rdflib.Graph()
g.parse(ontology, format='ttl')

ont_jsonld = g.serialize(format='json-ld', indent=4).decode()

ont_jsonld = json.loads(ont_jsonld)

with open("D:/oeg-projects/bimerr/ont.json", "w") as f:
    json.dump(ont_jsonld, f, indent=4)

f.close()

ont_dict = {}

# Namespaces
building = "https://bimerr.iot.linkeddata.es/def/building#"
ont_uri = "https://bimerr.iot.linkeddata.es/def/occupancy-profile#"
rdfs = "http://www.w3.org/2000/01/rdf-schema#"
owl = "http://www.w3.org/2002/07/owl#"

first_order_concepts = ["building", "occupant", "behavior", "thermalRequirements", "location"]
total_concepts = []

for element in ont_jsonld:

    try:
        element_type = element["@type"][0][element["@type"][0].find("#") + 1:].lower()
        if element_type == "class":
            concept = element["@id"][element["@id"].find("#") + 1:].lower()
            total_concepts.append(concept)
    except:
        continue

second_order_concepts = [concept for concept in total_concepts if concept not in first_order_concepts]
for element in ont_jsonld:

    class_name = element["@id"][element["@id"].find("#") + 1:].lower()

    if len(class_name) > 0:
        if class_name[0] == "_":
            continue

    if class_name in total_concepts:

        if class_name in ont_dict.keys():
            ont_dict[class_name]["standards"] = []
            ont_dict[class_name]["data_added"] = ""
            ont_dict[class_name]["date_deprecated"] = None
            ont_dict[class_name]["version"] = 1
            ont_dict[class_name]["related_terms"] = []
            ont_dict[class_name]["facet"] = {"cardinality": 1, "ordered": False, "sensitive": False}
        else:
            ont_dict[class_name] = {"standards": [], "data_added": "", "date_deprecated": None, "version": 1,
                                    "related_terms": [], "facet": {"cardinalityMax": 1, "ordered": False, "sensitive": False},
                                    "children": {}}
        # The zero inside the expression is because there could be more than one comment
        try:
            description = element[rdfs + "comment"][0]["@value"]
            ont_dict[class_name]["definition"] = description
            superclasses = element[rdfs + "subClassOf"]
            #ont_dict[class_name]["children"] = {}
        except:
            #ont_dict[class_name]["children"] = {}
            continue

        for superclass in superclasses:
            superclass_id = superclass["@id"]
            superclass_name = superclass["@id"][superclass["@id"].find("#") + 1:].lower()
            superclass_element = find_ontology_element(superclass_id, ont_jsonld)
            superclass_type = superclass_element["@type"][0]
            superclass_type_name = superclass_type[superclass_type.find("#") + 1:].lower()

            if superclass_type_name == "class":
                if superclass_name not in ont_dict.keys():
                    ont_dict[superclass_name] = {"children": {}}
                ont_dict[superclass_name]["children"][class_name] = {}
                continue

            property_id = superclass_element[owl + "onProperty"][0]["@id"]
            property_element = find_ontology_element(property_id, ont_jsonld)
            property_types = property_element["@type"]

            # One property could be of more than one type
            interesting_types = ["ObjectProperty", "DatatypeProperty"]
            property_names = [property_type[property_type.find("#") + 1:] for property_type in property_types]
            type = [type for type in property_names if type in interesting_types]
            type = type[0]

            if type == "ObjectProperty":
                try:
                    range_id = superclass_element[owl + "someValuesFrom"][0]["@id"]
                except:
                    range_id = superclass_element[owl + "allValuesFrom"][0]["@id"]

                range_name = range_id[range_id.find("#") + 1:].lower()
                ont_dict[class_name]["children"][range_name] = {}
                # break
            else:
                try:
                    children_flag = property_element[ont_uri + "children"][0]["@value"]
                    property_name = property_element["@id"][property_element["@id"].find("#") + 1:]
                    ont_dict[class_name]["children"][property_name] = {}
                    ont_dict[class_name]["children"][property_name]["definition"] = property_element[rdfs + "comment"][0][
                        "@value"]
                    try:
                        datatype = superclass_element[owl + "someValuesFrom"][0]["@id"]
                    except:
                        datatype = superclass_element[owl + "allValuesFrom"][0]["@id"]

                    datatype = datatype[datatype.find("#") + 1:]
                    ont_dict[class_name]["children"][property_name]["type"] = datatype
                    ont_dict[class_name]["children"][property_name]["standards"] = []
                    ont_dict[class_name]["children"][property_name]["data_added"] = ""
                    ont_dict[class_name]["children"][property_name]["date_deprecated"] = None
                    ont_dict[class_name]["children"][property_name]["version"] = 1
                    ont_dict[class_name]["children"][property_name]["related_terms"] = []
                    ont_dict[class_name]["children"][property_name]["facet"] = {"cardinality": 1, "ordered": False, "sensitive": False}

                    # break
                except:
                    continue

for i in ont_dict:
    print(i, ont_dict[i])

new_ont_dict = {}

for concept in first_order_concepts:

    if concept in ont_dict.keys():
        """
        first_order_children = []
        for i in ont_dict[concept]["children"]:
            if i in ont_dict.keys():
                first_order_children.append(i)
                #first_order_children = ont_dict[concept]["children"]
        """
        first_order_children = [i for i in ont_dict[concept]["children"] if i in ont_dict.keys()]

        # First level of children
        for children in first_order_children:
            if children not in first_order_concepts:
                ont_dict[concept]["children"][children] = ont_dict[children]
            elif children in first_order_concepts:
                ont_dict[concept]["children"][children]["type"] = {"$ref": "#/" + children}

        # Second level of children
        for children_01 in first_order_children:
            # Avoiding referenced concepts, because they dont have a children field
            try: second_order_children = ont_dict[concept]["children"][children_01]["children"]
            except: continue

            concepts_taked = first_order_concepts + first_order_children
            for children_02 in second_order_children:
                if children_02 in ont_dict.keys() and children_02 not in concepts_taked:
                    ont_dict[concept]["children"][children_01]["children"][children_02] = ont_dict[children_02]
                elif children_02 in ont_dict.keys() and children_02 in concepts_taked:
                    ont_dict[concept]["children"][children_01]["children"][children_02]["type"] = {"$ref": "#/" + children_02}

        for children_01 in first_order_children:

            try:
                second_order_children = ont_dict[concept]["children"][children_01]["children"]
                second_order_children = [i for i in second_order_children if i in ont_dict.keys()]

            except: continue
            concepts_taked = first_order_concepts + first_order_children

            for children_02 in second_order_children:

                try: third_order_children = ont_dict[concept]["children"][children_01]["children"][children_02]["children"]
                except: continue

                concepts_taked = first_order_concepts + first_order_children + second_order_children
                for children_03 in third_order_children:
                    if children_03 in ont_dict.keys() and children_03 not in concepts_taked:
                        ont_dict[concept]["children"][children_01]["children"][children_02]["children"][children_03] = ont_dict[children_03]
                    elif children_03 in ont_dict.keys() and children_03 in concepts_taked:
                        ont_dict[concept]["children"][children_01]["children"][children_02]["children"][children_03]["type"] = {
                            "$ref": "#/" + children_03}


        new_ont_dict[concept] = ont_dict[concept]

result = json.dumps(new_ont_dict, indent=4, separators=(',', ': '))

with open("./op_data_model.json", "w") as f:
    json.dump(new_ont_dict, f, indent=4, separators=(',', ': '))

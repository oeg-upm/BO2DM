# BIMERR to Data Model Converter (BO2DM)

Repository for the BIMERR to Data Model Converter which transforms an OWL ontology into the data model format of the BIMERR project.

## How to run it:

1. git clone the repository:

    `git clone https://github.com/oeg-upm/BO2DM.git`

2. Install dependencies:

    `pip install -r requirements.txt`

3. Make sure to generate the enriched version of the ontology and name it in the following way:

    **ns_enriched.ttl**
    
    Where **ns** is the namespace of the ontological model.

4. Run the converter.py script

    4.1. If you want to generate the data model using the original ontology published online.

    `python converter.py path/to/enriched/ontology path/to/output/datamodel`

    4.2. If you want to generate the data model using the original ontology from you local system.

    `python converter.py path/to/enriched/ontology path/to/output/datamodel -o path/to/original/ontology`
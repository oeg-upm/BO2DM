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

    `python converter.py path/to/enriched/ontology path/to/output/datamodel path/to/original/ontology`

    Notes:

    * If the path to the original ontology (not enriched version) is no included, the script will look for the published version of the ontology online.
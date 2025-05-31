from rdflib import URIRef, Namespace, term, RDF, RDFS, OWL

# Namespace definitions
BRICK: Namespace = Namespace("https://brickschema.org/schema/Brick#")
REC_CORE: Namespace = Namespace("https://w3id.org/rec/core/")
REC_PROPS: Namespace = Namespace("https://w3id.org/rec/props/")
S223: Namespace = Namespace("http://data.ashrae.org/standard223#")
NS_PROPS: Namespace = Namespace("https://w3id.org/rec/props/")
QUDT: Namespace = Namespace("http://qudt.org/schema/qudt/")
UNIT: Namespace = Namespace("http://qudt.org/vocab/unit/")

# Explicit URIRefs for RDF, RDFS, OWL terms to be used in graph operations
RDF_TYPE: URIRef = term.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
OWL_SAMEAS: URIRef = term.URIRef("http://www.w3.org/2002/07/owl#sameAs")
RDFS_LABEL: URIRef = term.URIRef("http://www.w3.org/2000/01/rdf-schema#label")
SKOS_PREF_LABEL: URIRef = term.URIRef("http://www.w3.org/2004/02/skos/core#prefLabel")

# rdflib namespaces for binding

PREFIX_DICT = {
    "brick": BRICK,
    "rec": REC_CORE,
    "s223": S223,
    "props": NS_PROPS,
    "qudt": QUDT,
    "unit": UNIT,
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
}

PREFIXES = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rec: <https://w3id.org/rec/core/>
    PREFIX s223: <http://data.ashrae.org/standard223#>
    PREFIX props: <https://w3id.org/rec/props/>
    PREFIX qudt: <http://qudt.org/schema/qudt/>
    PREFIX unit: <http://qudt.org/vocab/unit/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""

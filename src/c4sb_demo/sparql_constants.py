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
    "props": NS_PROPS, # Note: NS_PROPS is the same as REC_PROPS
    "qudt": QUDT,
    "unit": UNIT,
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    # Consider adding skos if used in queries and not just as URIRefs
    # "skos": SKOS_CORE_NS, # Assuming SKOS_CORE_NS = Namespace("http://www.w3.org/2004/02/skos/core#")
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

# SPARQL Query Definitions
# Each query is a dictionary with 'body' and 'path_graph_ttl'

QUERY_1 = {
    "body": """
SELECT ?ashrae_rtu ?ashrae_component ?ashrae_component_label ?ashrae_component_type
WHERE {
    ?brick_rtu_instance a brick:RTU .
    ?brick_rtu_instance owl:sameAs ?ashrae_rtu .
    ?ashrae_rtu a s223:AirHandlingUnit .
    ?ashrae_rtu s223:hasComponent ?ashrae_component .
    OPTIONAL { ?ashrae_component rdfs:label ?lbl . }
    OPTIONAL { ?ashrae_component s223:hasDescription ?desc . }
    BIND(COALESCE(?lbl, ?desc, "No Label/Description") AS ?ashrae_component_label)
    ?ashrae_component a ?ashrae_component_type .
    FILTER(?ashrae_component_type != s223:Component && ?ashrae_component_type != owl:NamedIndividual) 
}
""",
    "path_graph_ttl": PREFIXES + """
@prefix mybldg: <http://example.com/mybuilding#> .

mybldg:RTU-1 s223:hasComponent mybldg:RTU-1_SupplyFan .
mybldg:RTU-1_SupplyFan rdf:type s223:Fan .
mybldg:RTU-1 a s223:AirHandlingUnit .
brick:SomeBrickRTUForQ1 owl:sameAs mybldg:RTU-1 ;
    a brick:RTU .
"""
}

QUERY_2 = {
    "body": """
SELECT ?sensor_label ?zone_label ?rec_building_label ?rec_building_gross_area ?rec_room_label
WHERE {
    ?brick_building_instance a brick:Building .
    ?brick_building_instance owl:sameAs ?rec_building .
    ?brick_building_instance brick:hasPart ?brick_rtu_instance .

    ?brick_rtu_instance a brick:RTU .
    ?brick_rtu_instance brick:hasPoint ?sensor .
    ?brick_rtu_instance brick:feeds ?zone .

    ?sensor a brick:Discharge_Air_Temperature_Sensor .
    ?sensor rdfs:label ?sensor_label .
    
    ?zone rdfs:label ?zone_label .
    
    ?rec_building rdfs:label ?rec_building_label .
    OPTIONAL { ?rec_building props:hasArea ?area_bn_q2 . ?area_bn_q2 props:hasValue ?rec_building_gross_area . }
    
    OPTIONAL { 
        ?zone owl:sameAs ?rec_room . 
        ?rec_room rdfs:label ?rec_room_label .
    }
}
""",
    "path_graph_ttl": PREFIXES + """
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

brick:RTU_1_DAT_Sensor brick:hasLocation brick:Zone1 ;
    rdfs:label "RTU 1 Discharge Air Temperature Sensor" ;
    a brick:Discharge_Air_Temperature_Sensor .
brick:Zone1 brick:isPartOf rec:Room101 ;
    owl:sameAs rec:Room101 .
rec:Room101 rec:isPartOf rec:Building123 ;
    rdfs:label "Zone1's Room Label" .
rec:Building123 props:grossArea "50000.0"^^xsd:double ;
    rdfs:label "Main Building Label" .
brick:SomeBuildingForQ2 a brick:Building ;
    owl:sameAs rec:Building123 ;
    brick:hasPart brick:SomeRTUForQ2 .
brick:SomeRTUForQ2 a brick:RTU ;
    brick:hasPoint brick:RTU_1_DAT_Sensor ;
    brick:feeds brick:Zone1 .
"""
}

QUERY_3 = {
    "body": """
SELECT ?ashrae_rtu_description ?compressor_description ?brick_rtu_label ?rec_room_label ?rec_room_area
WHERE {
    ?ashrae_rtu a s223:AirHandlingUnit .
    ?ashrae_rtu s223:hasDescription ?ashrae_rtu_description .
    ?ashrae_rtu s223:hasComponent ?compressor .
    ?compressor a s223:Compressor .
    ?compressor s223:hasDescription ?compressor_description .
    ?brick_rtu owl:sameAs ?ashrae_rtu .
    ?brick_rtu rdfs:label ?brick_rtu_label .
    ?brick_rtu brick:feeds ?brick_hvac_zone .
    ?brick_hvac_zone owl:sameAs ?rec_room .
    ?rec_room rdfs:label ?rec_room_label .
    OPTIONAL { ?rec_room props:hasArea ?area_bn_q3 . ?area_bn_q3 props:hasValue ?rec_room_area . } 
}
""",
    "path_graph_ttl": PREFIXES + """
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

s223:RTU-1 s223:hasComponent s223:RTU-1-C1 .
s223:RTU-1-C1 rdf:type s223:Compressor .
brick:RTU_1 brick:hasLocation brick:MechanicalRoom1 .
brick:MechanicalRoom1 brick:isPartOf rec:Room101 .
rec:Room101 props:area "100"^^xsd:string .
s223:RTU-1 a s223:AirHandlingUnit ;
    s223:hasDescription "Rooftop Unit 1" .
s223:RTU-1-C1 s223:hasDescription "Compressor 1 for RTU-1" .
brick:RTU_1 owl:sameAs s223:RTU-1 ;
    rdfs:label "Brick RTU_1 Label" ;
    brick:feeds brick:ZoneServedByRTU1 .
brick:ZoneServedByRTU1 owl:sameAs rec:Room101 .
rec:Room101 rdfs:label "Room 101 Label" .
"""
}

QUERY_4 = {
    "body": """
SELECT ?ashrae_ahu_description ?voltage_value ?voltage_unit_label
WHERE {
    ?rec_room_instance a rec:Room .
    ?brick_zone_instance owl:sameAs ?rec_room_instance .
    ?brick_zone_instance a brick:HVAC_Zone .
    ?brick_ahu_instance brick:feeds ?brick_zone_instance .
    ?brick_ahu_instance owl:sameAs ?ashrae_ahu .

    ?ashrae_ahu a s223:AirHandlingUnit .
    ?ashrae_ahu s223:hasDescription ?ashrae_ahu_description .
    ?ashrae_ahu s223:hasConnectionPoint ?electrical_inlet .

    ?electrical_inlet a s223:InletConnectionPoint .
    ?electrical_inlet s223:hasMedium ?medium_instance .

    ?medium_instance s223:hasVoltage ?voltage_type_instance .
    ?voltage_type_instance s223:hasVoltage ?voltage_value_instance .
    ?voltage_value_instance s223:hasValue ?voltage_value .
    ?voltage_value_instance qudt:hasUnit ?voltage_unit_instance .
    OPTIONAL { ?voltage_unit_instance rdfs:label ?voltage_unit_label_temp . }
    BIND(COALESCE(?voltage_unit_label_temp, STRAFTER(STR(?voltage_unit_instance), STR(unit:))) AS ?voltage_unit_label)
}
""",
    "path_graph_ttl": PREFIXES + """
s223:RTU-1 s223:hasVoltage _:voltage_bnode_q4 .
_:voltage_bnode_q4 s223:hasValue "208.0"^^s223:numeric ;
    s223:hasUnit _:voltage_unit_instance_bnode_q4 .
_:voltage_unit_instance_bnode_q4 rdfs:label "V" ;
    rdf:type s223:UnitOfMeasure .
brick:Zone1 brick:isPartOf rec:Room101 .
brick:RTU_1 brick:feeds brick:Zone1 .
brick:RTU_1 owl:sameAs s223:RTU-1 .
rec:Room101 a rec:Room .
brick:Zone1 owl:sameAs rec:Room101 ;
    a brick:HVAC_Zone .
brick:RTU_1 a brick:RTU .
s223:RTU-1 a s223:AirHandlingUnit ;
    s223:hasDescription "Rooftop Unit 1" .
s223:RTU-1 s223:hasConnectionPoint _:cp_elec_inlet_q4_vis .
_:cp_elec_inlet_q4_vis a s223:InletConnectionPoint ;
    s223:hasMedium _:medium_inst_q4_vis .
_:medium_inst_q4_vis s223:hasVoltage _:voltage_bnode_q4 .
"""
}

# Example of an ASK query structure (if you had one)
# QUERY_ASK_EXAMPLE = {
# "body": """
# PREFIX brick: <https://brickschema.org/schema/Brick#>
# ASK WHERE {
# ?building a brick:Building .
# }
# """,
# "construct_where_patterns": """
# ?building a brick:Building .
# """
# }

# Example of a CONSTRUCT query structure (if you had one that wasn't just for path_graph)
# QUERY_CONSTRUCT_EXAMPLE = {
# "body": """
# PREFIX brick: <https://brickschema.org/schema/Brick#>
# CONSTRUCT { ?building a brick:Edifice . }
# WHERE {
# ?building a brick:Building .
# }
# """,
# "construct_where_patterns": None # Or the same as WHERE if needed for some other purpose
# }

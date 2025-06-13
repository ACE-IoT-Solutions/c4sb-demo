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
SELECT ?ashrae_rtu ?ashrae_component ?ashrae_component_label ?ashrae_component_type (COUNT(DISTINCT ?desk) AS ?affected_desks)
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

    # Link to REC room and count desks
    ?brick_rtu_instance brick:feeds ?brick_zone .
    ?brick_zone owl:sameAs ?rec_room .
    ?rec_room rec:containsAsset ?desk .
    ?desk a rec:Desk .
}
GROUP BY ?ashrae_rtu ?ashrae_component ?ashrae_component_label ?ashrae_component_type
""",
    "path_graph_ttl": PREFIXES + """
@prefix mybldg: <http://example.com/mybuilding#> .

mybldg:RTU-1 s223:hasComponent mybldg:RTU-1_SupplyFan .
mybldg:RTU-1_SupplyFan rdf:type s223:Fan .
mybldg:RTU-1 a s223:AirHandlingUnit .
brick:SomeBrickRTUForQ1 owl:sameAs mybldg:RTU-1 ;
    a brick:RTU ;
    brick:feeds brick:SomeZoneForQ1 . # Added feeds for path
brick:SomeZoneForQ1 owl:sameAs rec:SomeRoomForQ1 . # Added sameAs for path
rec:SomeRoomForQ1 rec:containsAsset rec:Desk1, rec:Desk2 ; # Added desks for path
    a rec:Room .
rec:Desk1 a rec:Desk .
rec:Desk2 a rec:Desk .
"""
}

QUERY_2 = {
    "body": """
SELECT ?sensor_label ?zone_label ?rec_building_label ?rec_building_gross_area (SUM(DISTINCT ?room_area_value) AS ?total_affected_area_sum) (COUNT(DISTINCT ?desk) AS ?affected_desks)
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
    OPTIONAL { ?rec_building props:grossArea ?rec_building_gross_area . } 
    
    ?zone owl:sameAs ?rec_room . 
    ?rec_room rdfs:label ?rec_room_label .
    
    ?rec_room props:hasArea [ props:hasValue ?room_area_value ] .
    ?rec_room rec:containsAsset ?desk .
    ?desk a rec:Desk .
}
GROUP BY ?sensor_label ?zone_label ?rec_building_label ?rec_building_gross_area ?rec_room_label
""",
    "path_graph_ttl": PREFIXES + """
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

brick:RTU_1_DAT_Sensor rdfs:label "RTU 1 Discharge Air Temperature Sensor" ;
    a brick:Discharge_Air_Temperature_Sensor ;
    brick:hasLocation brick:Zone1 .

brick:Zone1 a brick:HVAC_Zone ; 
    rdfs:label "Zone1 Label" ;
    brick:isPartOf rec:Room101 .

rec:Room101 a rec:Room ;
    rdfs:label "Room 101 Label" ;
    rec:isPartOf rec:Building123 ;
    rec:containsAsset rec:Desk1, rec:Desk2 ;
    props:hasArea [ props:hasValue "100.0"^^xsd:decimal ] .
rec:Desk1 a rec:Desk .
rec:Desk2 a rec:Desk .

brick:Zone2 a brick:HVAC_Zone ;
    rdfs:label "Zone2 Label" ;
    brick:isPartOf rec:Room102 .
rec:Room102 a rec:Room ;
    rdfs:label "Room 102 Label" ;
    rec:isPartOf rec:Building123 ;
    rec:containsAsset rec:Desk3, rec:Desk4, rec:Desk5 ;
    props:hasArea [ props:hasValue "150.0"^^xsd:decimal ] .
rec:Desk3 a rec:Desk .
rec:Desk4 a rec:Desk .
rec:Desk5 a rec:Desk .

rec:Building123 a rec:Building ;
    props:grossArea "50000.0"^^xsd:double ; # Changed props:hasArea [ props:hasValue ... ] to props:grossArea
    rdfs:label "Main Building Label" .

brick:SomeBuildingForQ2 a brick:Building ;
    owl:sameAs rec:Building123 ;
    brick:hasPart brick:RTU_1 .

brick:RTU_1 a brick:RTU ;
    brick:hasPoint brick:RTU_1_DAT_Sensor ;
    brick:feeds brick:Zone1, brick:Zone2 .
"""
}

QUERY_3 = {
    "body": """
SELECT ?ashrae_rtu_description ?compressor_description ?compressor_model_number ?brick_rtu_label ?rec_room_label ?rec_room_area (COUNT(DISTINCT ?desk) AS ?affected_desks)
WHERE {
    ?ashrae_rtu a s223:AirHandlingUnit .
    ?ashrae_rtu s223:hasDescription ?ashrae_rtu_description .
    ?ashrae_rtu s223:hasComponent ?compressor .
    ?compressor a s223:Compressor .
    ?compressor s223:hasDescription ?compressor_description .
    ?compressor s223:hasModelNumber ?compressor_model_number . 
    ?brick_rtu owl:sameAs ?ashrae_rtu .
    ?brick_rtu rdfs:label ?brick_rtu_label .
    ?brick_rtu brick:feeds ?brick_hvac_zone .
    ?brick_hvac_zone owl:sameAs ?rec_room .
    ?rec_room rdfs:label ?rec_room_label .
    OPTIONAL { ?rec_room props:hasArea ?area_bn_q3 . ?area_bn_q3 props:hasValue ?rec_room_area . } 
    
    # Count desks in the REC room
    ?rec_room rec:containsAsset ?desk .
    ?desk a rec:Desk .
}
GROUP BY ?ashrae_rtu_description ?compressor_description ?compressor_model_number ?brick_rtu_label ?rec_room_label ?rec_room_area
""",
    "path_graph_ttl": PREFIXES + """
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

s223:RTU-1 s223:hasComponent s223:RTU-1-C1 .
s223:RTU-1-C1 rdf:type s223:Compressor .
brick:RTU_1 brick:hasLocation brick:MechanicalRoom1 .
brick:MechanicalRoom1 brick:isPartOf rec:Room101 .
rec:Room101 props:area "100"^^xsd:string ; # Corrected from props:hasArea to props:area for consistency if it was a typo
    rec:containsAsset rec:DeskQ3_1, rec:DeskQ3_2 ; # Added desks for path
    a rec:Room .
rec:DeskQ3_1 a rec:Desk .
rec:DeskQ3_2 a rec:Desk .
s223:RTU-1 a s223:AirHandlingUnit ;
    s223:hasDescription "Rooftop Unit 1" .
s223:RTU-1-C1 s223:hasDescription "Compressor 1 for RTU-1" ;
    s223:hasModelNumber "COMP-MODEL-XYZ789" . 
brick:RTU_1 owl:sameAs s223:RTU-1 ;
    rdfs:label "Brick RTU_1 Label" ;
    brick:feeds brick:ZoneServedByRTU1 .
brick:ZoneServedByRTU1 owl:sameAs rec:Room101 .
rec:Room101 rdfs:label "Room 101 Label" .
"""
}

QUERY_4 = {
    "body": """
SELECT ?ashrae_ahu_description ?voltage_value ?voltage_unit_label (COUNT(DISTINCT ?desk) AS ?affected_desks)
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

    # Count desks in the REC room instance
    ?rec_room_instance rec:containsAsset ?desk .
    ?desk a rec:Desk .
}
GROUP BY ?ashrae_ahu_description ?voltage_value ?voltage_unit_label
""",
    "path_graph_ttl": PREFIXES + """
s223:RTU-1 s223:hasVoltage _:voltage_bnode_q4 .
_:voltage_bnode_q4 s223:hasValue "208.0"^^s223:numeric ; # Assuming s223:numeric is defined or use xsd:decimal/double
    s223:hasUnit _:voltage_unit_instance_bnode_q4 .
_:voltage_unit_instance_bnode_q4 rdfs:label "V" ;
    rdf:type s223:UnitOfMeasure . # Assuming s223:UnitOfMeasure is defined or use qudt:Unit
brick:Zone1 brick:isPartOf rec:Room101 . # Using owl:sameAs as per other queries
brick:RTU_1 brick:feeds brick:Zone1 .
brick:RTU_1 owl:sameAs s223:RTU-1 .
rec:Room101 a rec:Room ;
    rec:containsAsset rec:DeskQ4_1, rec:DeskQ4_2, rec:DeskQ4_3, rec:DeskQ4_4 ; # Added desks for path
    rdfs:label "Room 101 for Q4" .
rec:DeskQ4_1 a rec:Desk .
rec:DeskQ4_2 a rec:Desk .
rec:DeskQ4_3 a rec:Desk .
rec:DeskQ4_4 a rec:Desk .
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

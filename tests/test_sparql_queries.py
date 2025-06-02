import pytest
import rdflib
from pathlib import Path

from c4sb_demo.graph_operations import (
    create_combined_linked_graph,
    execute_sparql_query,
)
from c4sb_demo.sparql_constants import (
    BRICK, REC_CORE, REC_PROPS, S223,
    RDFS_LABEL, RDF_TYPE, OWL_SAMEAS,
    QUERY_1, 
    QUERY_2, 
    QUERY_3, 
    QUERY_4
)

XSD_DOUBLE = rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#double")
XSD_STRING = rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#string")

# Project root to locate data files
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data"
BRICK_FILE = DATA_PATH / "brick-building-simple.ttl"
REC_FILE = DATA_PATH / "rec-building-simple.ttl"
ASHRAE_FILE = DATA_PATH / "ashrae-223-rtu.ttl"
BRICK_ONTOLOGY_FILE = DATA_PATH / "validations" / "brick" / "Brick.ttl"
GENERATED_GRAPH_FILE = DATA_PATH / "generated" / "combined_graph.ttl"

# Fixture for the combined and linked graph
@pytest.fixture(scope="module")
def combined_graph(request): # Add request for finalizer
    g_combined = create_combined_linked_graph(
        brick_file=BRICK_FILE,
        rec_file=REC_FILE,
        ashrae_file=ASHRAE_FILE
    )
    if g_combined is None: 
        pytest.fail("Failed to create combined_graph in fixture: create_combined_linked_graph returned None.")
    # Ensure g_combined is a graph before parsing. This check might be redundant if create_combined_linked_graph type hints are correct
    # but added for robustness against potential linter confusion.
    if not isinstance(g_combined, rdflib.Graph):
        pytest.fail(f"Failed to create combined_graph: Expected rdflib.Graph, got {type(g_combined)}.")
    
    print("DEBUG: Temporarily skipping Brick Ontology parsing in test_sparql_queries.py fixture.")
    # if g_combined is not None and BRICK_ONTOLOGY_FILE.exists(): # Check if g_combined is not None
    #     try:
    #         # print(f"DEBUG: Parsing Brick Ontology: {BRICK_ONTOLOGY_FILE}")
    #         g_combined.parse(str(BRICK_ONTOLOGY_FILE), format="turtle")
    #         # print(f"DEBUG: Parsed Brick Ontology. Graph now has {len(g_combined)} triples.")
    #     except Exception as e:
    #         pytest.fail(f"Error parsing Brick ontology file {BRICK_ONTOLOGY_FILE}: {e}")
    # elif g_combined is None: # Added for clarity, though the earlier check should catch this
    #     pytest.fail("Cannot parse Brick ontology because combined_graph is None.")
    # else: # This means BRICK_ONTOLOGY_FILE does not exist
    #     pytest.fail(f"Brick ontology file not found: {BRICK_ONTOLOGY_FILE}.")
    
    def save_graph_on_teardown():
        if g_combined is not None and isinstance(g_combined, rdflib.Graph):
            try:
                # Ensure the directory exists
                GENERATED_GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
                g_combined.serialize(destination=str(GENERATED_GRAPH_FILE), format="turtle")
                print(f"DEBUG: Saved combined_graph to {GENERATED_GRAPH_FILE} during teardown.")
            except Exception as e:
                print(f"Error saving combined_graph to {GENERATED_GRAPH_FILE}: {e}")

    request.addfinalizer(save_graph_on_teardown)
    return g_combined


def assert_path_graph_basics(path_graph: rdflib.Graph, query_definition_for_debug: dict):
    assert len(path_graph) > 0, f"Path graph is empty. Query body:\\n{query_definition_for_debug['body']}"
    bound_prefixes = [p for p, _ in path_graph.namespaces()]
    assert "brick" in bound_prefixes, "brick prefix not bound in path_graph"
    assert "s223" in bound_prefixes, "s223 prefix not bound in path_graph"
    assert "rdfs" in bound_prefixes, "rdfs prefix not bound in path_graph"

# Test for Query 1 Results
def test_query_1_results(combined_graph):
    results_df, _ = execute_sparql_query(combined_graph, QUERY_1) # Ignore path_graph
    assert results_df is not None, "Query 1 returned None DataFrame"
    assert not results_df.empty, "Query 1 returned an empty DataFrame"
    assert len(results_df) == 5, f"Query 1 expected 5 components, got {len(results_df)}"
    component_labels = [str(label) for label in results_df['ashrae_component_label']]
    assert "Supply Fan for RTU-1" in component_labels
    assert "Compressor 1 for RTU-1" in component_labels

# Test for Query 1 Path Graph
def test_query_1_path_graph(combined_graph):
    _, path_graph = execute_sparql_query(combined_graph, QUERY_1) # Ignore results_df
    assert path_graph is not None, "Path graph should not be None for Query 1"
    assert_path_graph_basics(path_graph, QUERY_1)
    # Use actual URIs from the data
    rtu1_uri = rdflib.URIRef("http://example.com/mybuilding#RTU-1")
    supply_fan_uri = rdflib.URIRef("http://example.com/mybuilding#RTU-1_SupplyFan") 
    assert (rtu1_uri, S223.hasComponent, supply_fan_uri) in path_graph, \
        f"Path for RTU-1 to Supply Fan missing in Q1 path_graph. Path graph triples:\n{list(path_graph)}"
    assert (supply_fan_uri, RDF_TYPE, S223.Fan) in path_graph, \
        "Type for Supply Fan missing in Q1 path_graph"

# Test for Query 2 Results
def test_query_2_results(combined_graph):
    results_df, _ = execute_sparql_query(combined_graph, QUERY_2) # Ignore path_graph
    assert results_df is not None, "Query 2 returned None DataFrame"
    assert not results_df.empty, "Query 2 returned an empty DataFrame"
    assert str(results_df['sensor_label'].iloc[0]) == "RTU 1 Discharge Air Temperature Sensor"
    assert str(results_df['zone_label'].iloc[0]) == "HVAC Zone 1"

# Test for Query 2 Path Graph (temporarily disabled)
def test_query_2_path_graph(combined_graph): # Renamed from _test_query_2_path_graph
    _, path_graph = execute_sparql_query(combined_graph, QUERY_2) # Ignore results_df
    assert path_graph is not None, "Path graph should not be None for Query 2"
    assert_path_graph_basics(path_graph, QUERY_2) # Re-enabled assertion
    dat_sensor_uri = BRICK["RTU_1_DAT_Sensor"]
    zone1_uri = BRICK["Zone1"]
    rec_room101_uri = REC_CORE["Room101"]
    rec_building_uri = REC_CORE["Building123"]

    assert (dat_sensor_uri, BRICK.hasLocation, zone1_uri) in path_graph, \
        "Path for DAT Sensor location Zone1 missing in Q2 path_graph"
    assert (dat_sensor_uri, RDFS_LABEL, rdflib.Literal("RTU 1 Discharge Air Temperature Sensor")) in path_graph, \
        "Label for DAT Sensor missing in Q2 path_graph"
    assert (zone1_uri, BRICK.isPartOf, rec_room101_uri) in path_graph, \
        "Path for Zone1 partOf Room101 missing in Q2 path_graph"
    assert (rec_room101_uri, REC_CORE.isPartOf, rec_building_uri) in path_graph, \
        "Path for Room101 partOf Building123 missing in Q2 path_graph"
    assert (rec_building_uri, REC_PROPS.grossArea, rdflib.Literal("50000.0", datatype=XSD_DOUBLE)) in path_graph, \
        "Gross area for Building123 missing in Q2 path_graph"

# Test for Query 3 Results
def test_query_3_results(combined_graph):
    results_df, _ = execute_sparql_query(combined_graph, QUERY_3) # Ignore path_graph
    assert results_df is not None, "Query 3 returned None DataFrame"
    assert not results_df.empty, "Query 3 returned an empty DataFrame."
    assert "Rooftop Unit 1" in [str(val) for val in results_df['ashrae_rtu_description'].values]
    comp_desc_found = any("Compressor 1 for RTU-1" in str(desc) for desc in results_df['compressor_description'].values)
    assert comp_desc_found, "Query 3 did not find 'Compressor 1 for RTU-1' in compressor descriptions."

# Test for Query 3 Path Graph
def test_query_3_path_graph(combined_graph):
    _, path_graph = execute_sparql_query(combined_graph, QUERY_3) # Ignore results_df
    assert path_graph is not None, "Path graph should not be None for Query 3"
    assert_path_graph_basics(path_graph, QUERY_3)
    rtu1_s223_uri = S223["RTU-1"]
    compressor1_s223_uri = S223["RTU-1-C1"]
    rec_room101_uri = REC_CORE["Room101"]

    assert (rtu1_s223_uri, S223.hasComponent, compressor1_s223_uri) in path_graph, \
        "Path for s223:RTU-1 hasComponent s223:RTU-1-C1 missing in Q3 path_graph"
    assert (compressor1_s223_uri, RDF_TYPE, S223.Compressor) in path_graph, \
        "Type for s223:RTU-1-C1 missing in Q3 path_graph"
    assert (BRICK["RTU_1"], BRICK.hasLocation, BRICK["MechanicalRoom1"]) in path_graph, \
        "Path for brick:RTU_1 location MechanicalRoom1 missing in Q3 path_graph"
    assert (BRICK["MechanicalRoom1"], BRICK.isPartOf, rec_room101_uri) in path_graph, \
         "Path for brick:MechanicalRoom1 partOf rec:Room101 missing in Q3 path_graph"
    assert (rec_room101_uri, REC_PROPS.area, rdflib.Literal("100", datatype=XSD_STRING)) in path_graph, \
        "Area for Room101 missing in Q3 path_graph"

# Test for Query 4 Results
def test_query_4_results(combined_graph):
    results_df, _ = execute_sparql_query(combined_graph, QUERY_4) # Ignore path_graph
    assert results_df is not None, "Query 4 returned None DataFrame"
    assert not results_df.empty, "Query 4 returned an empty DataFrame."
    assert len(results_df) == 1, f"Query 4 expected 1 row, got {len(results_df)}"
    assert str(results_df['ashrae_ahu_description'].iloc[0]) == "Rooftop Unit 1"
    assert str(results_df['voltage_value'].iloc[0]) == "208.0"
    assert str(results_df['voltage_unit_label'].iloc[0]) == "V"

# Test for Query 4 Path Graph
def test_query_4_path_graph(combined_graph):
    _, path_graph = execute_sparql_query(combined_graph, QUERY_4) # Ignore results_df
    assert path_graph is not None, "Path graph should not be None for Query 4"
    assert_path_graph_basics(path_graph, QUERY_4)
    rtu1_s223_uri = S223["RTU-1"]
    voltage_bnode = None 
    for s, p, o in path_graph.triples((rtu1_s223_uri, S223.hasVoltage, None)):
        voltage_bnode = o
        break
    assert voltage_bnode is not None, "Voltage blank node not found in Q4 path_graph for RTU-1"
    assert isinstance(voltage_bnode, rdflib.BNode), "Voltage identifier is not a BNode"

    assert (voltage_bnode, S223.hasValue, rdflib.Literal("208.0", datatype=S223.numeric)) in path_graph, \
        "Voltage value missing in Q4 path_graph"
    
    voltage_unit_instance_bnode = None
    for s, p, o in path_graph.triples((voltage_bnode, S223.hasUnit, None)):
        voltage_unit_instance_bnode = o
        break
    assert voltage_unit_instance_bnode is not None, "Voltage unit instance bnode not found in Q4 path_graph"
    assert isinstance(voltage_unit_instance_bnode, rdflib.BNode), "Voltage unit instance is not a BNode"
    assert (voltage_unit_instance_bnode, RDFS_LABEL, rdflib.Literal("V")) in path_graph, \
        "Voltage unit label 'V' missing in Q4 path_graph"
    assert (voltage_unit_instance_bnode, RDF_TYPE, S223.UnitOfMeasure) in path_graph, \
        "Voltage unit type s223:UnitOfMeasure missing in Q4 path_graph"

    rec_room101_uri = REC_CORE["Room101"]
    brick_zone1_uri = BRICK["Zone1"]
    brick_rtu1_uri = BRICK["RTU_1"]
    assert (brick_zone1_uri, BRICK.isPartOf, rec_room101_uri) in path_graph, \
        "Path brick:Zone1 isPartOf rec:Room101 missing in Q4 path_graph"
    assert (brick_rtu1_uri, BRICK.feeds, brick_zone1_uri) in path_graph, \
        "Path brick:RTU_1 feeds brick:Zone1 missing in Q4 path_graph"
    assert (brick_rtu1_uri, OWL_SAMEAS, rtu1_s223_uri) in path_graph, \
        "owl:sameAs link between brick:RTU_1 and s223:RTU-1 missing in Q4 path_graph"

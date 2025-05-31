import rdflib
from rdflib.namespace import RDF, RDFS, OWL, Namespace 
from rdflib.term import URIRef 

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Union # Removed cast, not needed with new approach
import re

from c4sb_demo.sparql_constants import (
    BRICK,      
    REC_CORE,   
    S223,       
    NS_PROPS,   
    QUDT,       
    UNIT,       
    RDF_TYPE,
    OWL_SAMEAS,
    PREFIX_DICT
)

# Ensure that the imported RDF, RDFS, OWL are indeed Namespace objects for binding
# If they are imported as something else (e.g. just a base URI string from another module),
# they need to be correctly defined as rdflib.Namespace for graph.bind()
# For example:
# RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
# RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
# OWL = Namespace("http://www.w3.org/2002/07/owl#")
# These are correctly imported from rdflib.namespace, so they are Namespace objects.

def load_graph(file_path: Path) -> Optional[rdflib.Graph]:
    """Loads an RDF graph from a file."""
    if not file_path or not file_path.exists():
        # print(f\"DEBUG: File not found or None: {file_path}\")
        return None
    g = rdflib.Graph()
    try:
        # print(f\"DEBUG: Parsing file: {file_path}\")
        g.parse(str(file_path), format=rdflib.util.guess_format(str(file_path)) or "turtle")
        # print(f\"DEBUG: Parsed {file_path}, graph now has {len(g)} triples.\")
        return g
    except Exception as e:
        print(f"Error loading graph from {file_path}: {e}")
        return None

# Helper function to safely add a prefix and bind it to the graph (module level)
def _safe_bind_prefix(graph: rdflib.Graph, prefix: str, namespace_val: Union[Namespace, URIRef, str]):
    """
    Safely binds a prefix to a namespace in the graph.
    If the prefix is already bound to a different namespace URI, it overrides.
    If already bound to the same namespace URI, it does nothing.
    """
    current_ns_uri_str = None
    for p, bound_ns_uriref in graph.namespaces():
        if p == prefix:
            current_ns_uri_str = str(bound_ns_uriref)
            break

    target_ns_uri_str = None
    # The namespace_val for binding should be the base URI string or a Namespace object.
    # If it's a URIRef like RDF.type, we should bind its namespace, not the URIRef itself.
    if isinstance(namespace_val, Namespace):
        target_ns_uri_str = str(namespace_val)
        # graph.bind expects a string or Namespace for the namespace argument
        namespace_to_bind = namespace_val
    elif isinstance(namespace_val, URIRef): # e.g. if someone passed BRICK.Building
        # We should bind the namespace of this URIRef, not the URIRef itself.
        # This part might need adjustment based on how BRICK, REC_CORE etc are defined.
        # Assuming BRICK, REC_CORE etc are Namespace objects, this case is less likely for them.
        # For RDF, RDFS, OWL, they are Namespace objects from rdflib.namespace.
        # If namespace_val is something like RDF.type, we bind RDF.
        # This logic is tricky if we don't know if namespace_val is a base Namespace or a specific term.
        # For now, let's assume if it's a URIRef, it's intended as the namespace URI itself.
        target_ns_uri_str = str(namespace_val)
        namespace_to_bind = str(namespace_val) # Bind the string URI
    elif isinstance(namespace_val, str):
        try:
            URIRef(namespace_val) # Validate
            target_ns_uri_str = namespace_val
            namespace_to_bind = namespace_val # Bind the string URI
        except ValueError: # Catch ValueError for invalid URI strings
            # print(f"Warning: Invalid URI string for prefix {prefix}: {namespace_val}")
            return 
        except Exception: # Fallback for other unexpected validation issues
            # print(f"Warning: General error validating URI for prefix {prefix}: {namespace_val}")
            return
    else:
        # print(f"Warning: Invalid namespace type for prefix {prefix}: {type(namespace_val)}")
        return 

    if current_ns_uri_str != target_ns_uri_str: 
        graph.bind(prefix, namespace_to_bind, override=True)


# SPARQL Query Definitions (cleaned and generalized)
QUERY_1_BODY = """
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
"""

QUERY_2_BODY = """
SELECT ?sensor_label ?zone_label ?rec_building_label ?rec_building_gross_area ?rec_room_label
WHERE {
    ?brick_building_instance a brick:Building .
    ?brick_building_instance owl:sameAs ?rec_building .
    ?brick_building_instance brick:hasPart ?brick_rtu_instance .

    ?brick_rtu_instance a brick:RTU ;
                        brick:hasPoint ?sensor ;
                        brick:feeds ?zone .

    ?sensor a brick:Discharge_Air_Temperature_Sensor ;
            rdfs:label ?sensor_label .
    
    ?zone rdfs:label ?zone_label .
    
    ?rec_building rdfs:label ?rec_building_label .
    OPTIONAL { ?rec_building props:hasArea [ props:hasValue ?rec_building_gross_area ] . }
    
    OPTIONAL { 
        ?zone owl:sameAs ?rec_room . 
        ?rec_room rdfs:label ?rec_room_label .
    }
}
"""

QUERY_3_BODY = """
SELECT ?ashrae_rtu_description ?compressor_description ?brick_rtu_label ?rec_room_label ?rec_room_area
WHERE {
    ?ashrae_rtu a s223:AirHandlingUnit ;
                s223:hasDescription ?ashrae_rtu_description ;
                s223:hasComponent ?compressor .
    ?compressor a s223:Compressor ;
                s223:hasDescription ?compressor_description .
    ?brick_rtu owl:sameAs ?ashrae_rtu .
    ?brick_rtu rdfs:label ?brick_rtu_label ;
               brick:feeds ?brick_hvac_zone .
    ?brick_hvac_zone owl:sameAs ?rec_room .
    ?rec_room rdfs:label ?rec_room_label .
    OPTIONAL { ?rec_room props:hasArea [ props:hasValue ?rec_room_area ] . } 
}
"""

QUERY_4_BODY = """
SELECT ?ashrae_ahu_description ?voltage_value ?voltage_unit_label
WHERE {
    ?rec_room_instance a rec:Room .
    ?brick_zone_instance owl:sameAs ?rec_room_instance ;
                         a brick:HVAC_Zone .
    ?brick_ahu_instance brick:feeds ?brick_zone_instance ;
                        owl:sameAs ?ashrae_ahu .

    ?ashrae_ahu a s223:AirHandlingUnit ;
                s223:hasDescription ?ashrae_ahu_description ;
                s223:hasConnectionPoint ?electrical_inlet .

    ?electrical_inlet a s223:InletConnectionPoint ;
                      s223:hasMedium ?medium_instance .

    # ?medium_instance a s223:Electricity . # This was too restrictive
    ?medium_instance s223:hasVoltage ?voltage_type_instance .
    ?voltage_type_instance s223:hasVoltage ?voltage_value_instance .
    ?voltage_value_instance s223:hasValue ?voltage_value .
    # ?voltage_value_instance s223:hasUnit ?voltage_unit_instance . # QUDT is used in s223 data
    ?voltage_value_instance qudt:hasUnit ?voltage_unit_instance .
    OPTIONAL { ?voltage_unit_instance rdfs:label ?voltage_unit_label_temp . }
    BIND(COALESCE(?voltage_unit_label_temp, STRAFTER(STR(?voltage_unit_instance), STR(unit:))) AS ?voltage_unit_label)
}
"""

def get_where_clause_content(sparql_query_body: str) -> Optional[str]:
    """
    Extracts the content of the main WHERE clause from a SPARQL query body.
    Handles basic nested braces within the WHERE clause.
    Filters out OPTIONAL, BIND, and FILTER clauses for CONSTRUCT WHERE compatibility.
    """
    # print(f"DEBUG get_where_clause_content: Input query body:\\n{sparql_query_body}") # Uncomment for debugging
    # Find the start of the WHERE clause, case insensitive
    # Regex looks for WHERE, optional whitespace, then {
    where_match = re.search(r"WHERE\s*\{", sparql_query_body, re.IGNORECASE | re.DOTALL)
    if not where_match:
        print("DEBUG get_where_clause_content: No WHERE clause found.") # Added
        return None

    # Index of the opening brace '{'
    start_brace_index = where_match.end() - 1 
    # Content starts after this brace
    content_start_index = start_brace_index + 1
    
    brace_level = 0
    # Iterate from the position of the first opening brace in the relevant part of the string
    for i, char in enumerate(sparql_query_body[start_brace_index:]):
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0:
                # Found the matching closing brace for the main WHERE clause
                # The content is from after the first '{' (content_start_index)
                # to before this closing '}' (start_brace_index + i)
                extracted_content = sparql_query_body[content_start_index : start_brace_index + i].strip()
                # Filter out OPTIONAL, BIND, and FILTER for CONSTRUCT WHERE compatibility
                filtered_content = _filter_for_construct_where(extracted_content)
                # print(f"DEBUG get_where_clause_content: Extracted content:\\n{filtered_content}") # Uncomment for debugging
                return filtered_content
    
    print("DEBUG get_where_clause_content: Matching closing brace not found.") # Added
    return None # Should not happen if query is well-formed and WHERE clause exists

def _filter_for_construct_where(where_content: str) -> str:
    """
    Filters WHERE clause content to be compatible with CONSTRUCT WHERE.
    Removes OPTIONAL, BIND, and FILTER clauses, and attempts to correctly
    format triple patterns, including those using semicolon notation.
    """
    content = where_content
    
    # Remove OPTIONAL blocks (including nested braces)
    import re # Ensure re is available
    while True:
        optional_match = re.search(r'OPTIONAL\\s*\\{', content, re.IGNORECASE | re.DOTALL)
        if not optional_match:
            break
        
        start = optional_match.start()
        brace_start = optional_match.end() - 1
        brace_count = 0
        end = brace_start # Initialize end here
        
        # Find matching brace for the OPTIONAL block
        for i, char in enumerate(content[brace_start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = brace_start + i + 1
                    break
        if end == brace_start: # Safety check if matching brace wasn't found
            # This indicates a malformed OPTIONAL block or an issue with the loop
            # For now, break to avoid infinite loop if 'end' isn't updated
            print(f"Warning: Could not find matching brace for OPTIONAL block starting at index {start}.")
            break 
            
        content = content[:start] + content[end:]
    
    lines = content.split('\\n')
    filtered_lines = []
    current_subject = None  # Initialize current_subject outside the loop

    for line_content in lines: # Renamed 'line' to 'line_content' to avoid conflict with 'lines' list
        line_stripped = line_content.strip()

        if (not line_stripped or line_stripped.startswith('#') or
            line_stripped.upper().startswith('BIND') or 
            line_stripped.upper().startswith('FILTER')):
            # For BIND/FILTER, we might not want to reset current_subject if they are inline
            # However, for simplicity now, let's continue.
            continue
        
        # Heuristic to identify if a line starts with a subject-like token
        # (variable, IRI, or prefixed name)
        def looks_like_subject(token):
            return token.startswith('?') or token.startswith('<') or \
                   (':' in token and not token.startswith('_:')) or \
                   token.startswith('_:')

        # Heuristic to identify if a line starts with a predicate-like token
        # (variable, IRI, prefixed name, or 'a')
        def looks_like_predicate(token):
            return looks_like_subject(token) or token.lower() == 'a'

        if ';' in line_stripped:
            parts = line_stripped.split(';')
            for i, part_str in enumerate(parts):
                part_stripped = part_str.strip()
                if not part_stripped:
                    continue

                tokens = part_stripped.split(None, 2 # Max split: subject, predicate, object
                )
                
                if i == 0: # First part of a semicolon list, e.g., "?s ?p1 ?o1"
                    if len(tokens) >= 2 and looks_like_subject(tokens[0]):
                        current_subject = tokens[0]
                        # Reconstruct the triple carefully
                        if len(tokens) == 3: # s p o
                            triple = f"{tokens[0]} {tokens[1]} {tokens[2]}"
                            if not triple.endswith('.'): 
                                triple += " ."
                            filtered_lines.append(triple)
                        elif len(tokens) == 2: # s p (object might be implied or missing)
                            # This case is tricky if object is truly missing before ';'
                            # For now, assume it's a complete s p o or s p.
                            # If it's just 's p', it might be an error or part of a path
                            # Let's assume 's p o' for simplicity if 3 tokens, else it's more complex
                            # This part of the original logic was complex and potentially problematic.
                            # For now, we rely on having s p o.
                            pass # Handled by len(tokens) == 3
                    else: # Malformed first part
                        current_subject = None # Reset if first part isn't a clear subject start
                        if part_stripped: # If it's not empty, add it as is (risky)
                             final_part = part_stripped
                             if not final_part.endswith('.'): 
                                 final_part += " ."
                             filtered_lines.append(final_part)
                else: # Subsequent parts, e.g., "?p2 ?o2"
                    if current_subject and len(tokens) >= 2 and looks_like_predicate(tokens[0]): # p o
                        predicate = tokens[0]
                        obj = tokens[1] if len(tokens) > 1 else ""
                        triple = f"{current_subject} {predicate} {obj}"
                        if not triple.endswith('.'): 
                            triple += " ."
                        filtered_lines.append(triple)
                    elif part_stripped: # No current subject or malformed p o
                         final_part = part_stripped
                         if not final_part.endswith('.'): 
                             final_part += " ."
                         filtered_lines.append(final_part) # Risky: add as is
        else: # No semicolon in line_stripped
            tokens = line_stripped.split(None, 2) # s p o or p o or just s
            if len(tokens) >= 1:
                first_token = tokens[0]
                if looks_like_subject(first_token) and len(tokens) >= 3: # Looks like a new s p o triple
                    current_subject = first_token
                    final_line = line_stripped
                    if not final_line.endswith('.'): 
                        final_line += " ."
                    filtered_lines.append(final_line)
                elif current_subject and looks_like_predicate(first_token) and len(tokens) >= 2 : # Looks like p o, needs current_subject
                    final_line = f"{current_subject} {line_stripped}"
                    if not final_line.endswith('.'): 
                        final_line += " ."
                    filtered_lines.append(final_line)
                elif line_stripped: # Fallback: not clearly s p o or p o with active subject. Add as is.
                    # This could be a full triple not caught above, or problematic.
                    # Try to determine if it's a new subject if current_subject is None
                    if not current_subject and looks_like_subject(first_token) and len(tokens)>=2:
                        current_subject = first_token # Tentatively set subject
                    
                    final_line = line_stripped
                    if not final_line.endswith('.'): 
                        final_line += " ."
                    filtered_lines.append(final_line)
            elif line_stripped: # e.g. just a single token, unlikely valid but preserve
                filtered_lines.append(line_stripped)
                
    return '\\n'.join(filtered_lines)

def execute_sparql_query(graph: rdflib.Graph, query_body: str) -> tuple[Optional[pd.DataFrame], Optional[rdflib.Graph]]:
    if graph is None:
        print("DEBUG: execute_sparql_query called with None graph.")
        return None, None
    
    print(f"DEBUG: Input graph to execute_sparql_query has {len(graph)} triples.")
    # print(f"DEBUG: Query body:\\n{query_body}") # Uncomment to see full query

    path_graph = rdflib.Graph()

    # Bind all essential prefixes first
    if PREFIX_DICT:
        for prefix_key, namespace_obj_from_dict in PREFIX_DICT.items():
            _safe_bind_prefix(path_graph, prefix_key, Namespace(str(namespace_obj_from_dict)))
    
    # Also bind from main graph namespaces
    for p, ns_uriref_from_main_graph in graph.namespaces(): 
        _safe_bind_prefix(path_graph, p, ns_uriref_from_main_graph)
    
    # Debug: check what prefixes are bound in path_graph
    # print(f"DEBUG: Path graph prefixes: {[p for p, _ in path_graph.namespaces()]}")

    try:
        results: rdflib.query.Result = graph.query(query_body, initNs=PREFIX_DICT)
        print(f"DEBUG: Query results type: {results.type}")
        df: Optional[pd.DataFrame] = None

        if results.type == 'ASK':
            df = pd.DataFrame([{'ASK_RESULT': results.askAnswer}])
            print(f"DEBUG ASK result: {results.askAnswer}")
            where_content = get_where_clause_content(query_body)
            if where_content:
                construct_query_for_ask = f"CONSTRUCT WHERE {{ {where_content} }}"
                # print(f"DEBUG ASK CONSTRUCT query:\\\\n{construct_query_for_ask}") # Uncomment for debugging
                try:
                    path_construct_results = graph.query(construct_query_for_ask, initNs=PREFIX_DICT)
                    if path_construct_results.graph:
                        print(f"DEBUG ASK: path_construct_results.graph has {len(path_construct_results.graph)} triples.")
                        path_graph += path_construct_results.graph
                    else:
                        print("DEBUG ASK: path_construct_results.graph is None or empty.") # Added
                except Exception as e_construct:
                    print(f"Error constructing path_graph for ASK query: {e_construct}\\\\nQuery: {construct_query_for_ask[:300]}...")

        elif results.type == 'SELECT':
            data: List[Dict[str, Any]] = []
            select_vars = results.vars if results.vars is not None else []
            if results.bindings: 
                for binding_idx, binding in enumerate(results.bindings):
                    current_row_dict: Dict[str, Any] = {}
                    for var_name in select_vars: 
                        value = binding.get(var_name)
                        current_row_dict[str(var_name)] = value if value is not None else ""
                    data.append(current_row_dict)
                df = pd.DataFrame(data)
                print(f"DEBUG SELECT: DataFrame created with {len(df)} rows.")
            else: 
                columns_list = [str(var) for var in select_vars]
                if columns_list:
                    df = pd.DataFrame(columns=pd.Index(columns_list))
                else:
                    df = pd.DataFrame()
                print("DEBUG SELECT: No bindings, empty DataFrame with defined columns created.")

            # Enable path graph construction for SELECT queries
            where_content = get_where_clause_content(query_body)
            if where_content:
                construct_query_for_select = f"CONSTRUCT WHERE {{ {where_content} }}"
                # print(f"DEBUG SELECT CONSTRUCT query:\\\\n{construct_query_for_select}") # Uncomment for debugging
                try:
                    path_construct_results = graph.query(construct_query_for_select, initNs=PREFIX_DICT)
                    if path_construct_results.graph:
                        print(f"DEBUG SELECT: path_construct_results.graph has {len(path_construct_results.graph)} triples.")
                        path_graph += path_construct_results.graph
                    else:
                        print("DEBUG SELECT: path_construct_results.graph is None or empty.")
                except Exception as e_construct:
                    print(f"Error constructing path_graph for SELECT query: {e_construct}\\\\\\nQuery: {construct_query_for_select[:300]}...")
            else:
                print("DEBUG SELECT: No WHERE clause content found for path_graph construction.")


        elif results.type == 'CONSTRUCT':
            if results.graph is not None:
                path_graph += results.graph 
                print(f"DEBUG CONSTRUCT: Added {len(results.graph)} triples to path_graph from query result.")
                construct_df_data: List[Dict[str, Any]] = [] 
                for s, p, o in results.graph:
                    construct_df_data.append({'subject': str(s), 'predicate': str(p), 'object': str(o)})
                df = pd.DataFrame(construct_df_data)
            else: 
                df = pd.DataFrame()
                print("DEBUG CONSTRUCT: results.graph is None.")
        
        elif results.type == 'DESCRIBE': 
            if results.graph is not None:
                path_graph += results.graph 
                print(f"DEBUG DESCRIBE: Added {len(results.graph)} triples to path_graph from query result.")
                describe_df_data: List[Dict[str, Any]] = [] 
                for s, p, o in results.graph:
                    describe_df_data.append({'subject': str(s), 'predicate': str(p), 'object': str(o)})
                if describe_df_data:
                    df = pd.DataFrame(describe_df_data)
                elif results.vars: 
                    df = pd.DataFrame([{'described_uri': str(v)} for v in results.vars])
                else:
                    df = pd.DataFrame() 
            elif results.vars: 
                 df = pd.DataFrame([{'described_uri': str(v)} for v in results.vars])
            else: 
                df = pd.DataFrame()
                print("DEBUG DESCRIBE: results.graph is None and no vars.")
        
        else:
            print(f"Unhandled query result type: {results.type}") 
            return None, None 

        print(f"DEBUG: Returning DataFrame with {len(df) if df is not None else 'None'} rows and path_graph with {len(path_graph)} triples.")
        return df, path_graph

    except Exception as e:
        # print(f"Error executing SPARQL query (using initNs): {e}") # Original line
        print(f"Error executing SPARQL query: {e}") # Modified line
        return None, None


def create_combined_linked_graph(
    brick_file: Path, 
    rec_file: Path, 
    ashrae_file: Path,
    additional_ttl_files: Optional[List[Path]] = None
) -> Optional[rdflib.Graph]:
    g = rdflib.Graph()
    print("DEBUG: Initializing combined graph.") # Re-enabled

    # Bind all known prefixes to the graph using PREFIX_DICT from sparql_constants
    # This assumes PREFIX_DICT contains the definitive set of prefixes and their Namespace objects
    if PREFIX_DICT:
        for prefix_key, namespace_obj_from_dict in PREFIX_DICT.items():
            # Values in PREFIX_DICT should be rdflib.Namespace objects
            _safe_bind_prefix(g, prefix_key, namespace_obj_from_dict)
    
    # If there are any prefixes critical for tests that might not be in PREFIX_DICT
    # or need a very specific Namespace object not aliased in PREFIX_DICT,
    # they can be added here. For example, if `rec` must specifically be `REC_CORE`
    # and `PREFIX_DICT["rec"]` might be different (though unlikely based on current sparql_constants.py)
    # _safe_bind_prefix(g, "rec", REC_CORE) # This should be covered by PREFIX_DICT if "rec": REC_CORE is there.

    # The test expects "exash", "exb" - these are not in the current PREFIX_DICT
    # We need to define them or add them to PREFIX_DICT if they are standard for this project.
    # For now, let's assume they are not standard and the test needs adjustment or these namespaces need definition.
    # If they were defined (e.g., EXASH = Namespace("http://example.com/exash#") ), we would bind them:
    # _safe_bind_prefix(g, "exash", EXASH)
    # _safe_bind_prefix(g, "exb", EXB)

    files_to_load = [brick_file, rec_file, ashrae_file]
    if additional_ttl_files:
        files_to_load.extend(additional_ttl_files)

    try:
        for ttl_file in files_to_load:
            if ttl_file and ttl_file.exists():
                print(f"DEBUG: Parsing file: {ttl_file}") # Re-enabled
                g.parse(str(ttl_file), format="turtle")
                print(f"DEBUG: Parsed {ttl_file}, graph now has {len(g)} triples.") # Re-enabled
            else:
                print(f"DEBUG: File not found or None: {ttl_file}") # Re-enabled
    except Exception as e:
        print(f"Error loading TTL files: {e}")
        return None

    print(f"DEBUG: All files parsed. Total triples before linking: {len(g)}") # Re-enabled

    # Link Buildings: Brick Building to REC Building
    brick_buildings = list(g.subjects(predicate=RDF_TYPE, object=BRICK.Building))
    rec_buildings = list(g.subjects(predicate=RDF_TYPE, object=REC_CORE.Building))
    print(f"DEBUG: Found Brick Buildings: {brick_buildings}") # Added
    print(f"DEBUG: Found REC Buildings: {rec_buildings}") # Added
    if brick_buildings and rec_buildings:
        # Assuming there's only one of each for simplicity in this demo data
        # And that they correspond to each other.
        # In a real scenario, you might need more sophisticated matching logic.
        g.add((brick_buildings[0], OWL_SAMEAS, rec_buildings[0]))
        print(f"DEBUG: Added owl:sameAs between {brick_buildings[0]} and {rec_buildings[0]}") # Added
    else:
        print("DEBUG: No Brick or REC buildings found to link, or one list is empty.") # Modified

    # Link RTUs: Brick RTU to ASHRAE 223 RTU (AirHandlingUnit)
    brick_rtus = list(g.subjects(predicate=RDF_TYPE, object=BRICK.RTU))
    ashrae_rtus = list(g.subjects(predicate=RDF_TYPE, object=S223.AirHandlingUnit))
    print(f"DEBUG: Found Brick RTUs: {brick_rtus}") # Added
    print(f"DEBUG: Found ASHRAE AHUs: {ashrae_rtus}") # Added

    if brick_rtus and ashrae_rtus:
        # Assuming there's only one of each for simplicity in this demo data
        g.add((brick_rtus[0], OWL_SAMEAS, ashrae_rtus[0]))
        print(f"DEBUG: Added owl:sameAs between {brick_rtus[0]} and {ashrae_rtus[0]}") # Added
    else:
        print("DEBUG: No Brick RTUs or ASHRAE AHUs found to link, or one list is empty.") # Modified

    # Link HVAC Zones (Brick) to Rooms (REC)
    brick_hvac_zones = list(g.subjects(predicate=RDF_TYPE, object=BRICK.HVAC_Zone))
    rec_rooms = list(g.subjects(predicate=RDF_TYPE, object=REC_CORE.Room))
    print(f"DEBUG: Found Brick HVAC Zones: {brick_hvac_zones}") # Added
    print(f"DEBUG: Found REC Rooms: {rec_rooms}") # Added

    if brick_hvac_zones and rec_rooms:
        # Assuming one-to-one mapping for simplicity
        g.add((brick_hvac_zones[0], OWL_SAMEAS, rec_rooms[0]))
        print(f"DEBUG: Added owl:sameAs between {brick_hvac_zones[0]} and {rec_rooms[0]}") # Added
    else:
        print("DEBUG: No Brick HVAC Zones or REC Rooms found to link, or one list is empty.") # Modified
    
    # Link Mechanical Room (Brick) to Room (REC) - if applicable
    brick_mech_rooms = list(g.subjects(predicate=RDF_TYPE, object=BRICK.Mechanical_Room))
    print(f"DEBUG: Found Brick Mechanical Rooms: {brick_mech_rooms}") # Added
    if brick_mech_rooms and rec_rooms:
        target_rec_room_for_mech = rec_rooms[0]
        mech_room_is_hvac_zone = bool(brick_hvac_zones and brick_mech_rooms[0] == brick_hvac_zones[0])

        if mech_room_is_hvac_zone and len(rec_rooms) > 1:
            target_rec_room_for_mech = rec_rooms[1]

        if not (mech_room_is_hvac_zone and len(rec_rooms) <= 1):
            if (brick_mech_rooms[0], OWL_SAMEAS, target_rec_room_for_mech) not in g:
                g.add((brick_mech_rooms[0], OWL_SAMEAS, target_rec_room_for_mech))
                print(f"DEBUG: Linked Brick Mechanical Room {brick_mech_rooms[0]} to REC Room {target_rec_room_for_mech}") # Re-enabled
            else:
                print(f"DEBUG: Link for Brick Mechanical Room {brick_mech_rooms[0]} to REC Room {target_rec_room_for_mech} already exists.") # Re-enabled
        elif mech_room_is_hvac_zone and len(rec_rooms) <=1 : # Explicitly re-enable this print
            print(f"DEBUG: Brick Mechanical Room {brick_mech_rooms[0]} is also the linked HVAC zone, and no other REC rooms to link.") # Re-enabled
        
    else: # Explicitly re-enable this print
        print("DEBUG: No Brick Mechanical Rooms or REC Rooms found for specific linking.") # Re-enabled

    # Add inverse hasPart relationships for isPartOf
    print("DEBUG: Adding inverse hasPart relationships...")
    isPartOf_triples = list(g.triples((None, BRICK.isPartOf, None)))
    for part, _, whole in isPartOf_triples:
        g.add((whole, BRICK.hasPart, part))
        # print(f"DEBUG: Added hasPart: {whole} -> {part}")  # Commented out for cleaner output

    print(f"DEBUG: Graph after linking and inverse relationships. Total triples: {len(g)}") # Re-enabled
    return g

# Example usage (optional, for testing or direct script execution)
if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent.parent 
    data_dir = project_root / "data"
    
    brick_ttl = data_dir / "brick-building-simple.ttl"
    rec_ttl = data_dir / "rec-building-simple.ttl"
    ashrae_ttl = data_dir / "ashrae-223-rtu.ttl"
    
    combined_graph = create_combined_linked_graph(
        brick_file=brick_ttl, 
        rec_file=rec_ttl, 
        ashrae_file=ashrae_ttl
    )
    
    if combined_graph:
        print(f"Combined graph created with {len(combined_graph)} triples.")
        # Example: Test Query 1
        # print("\\nTesting Query 1...")
        # q1_df, q1_path = execute_sparql_query(combined_graph, QUERY_1_BODY)
        # if q1_df is not None:
        #     print("Query 1 Results:")
        #     print(q1_df.head())
        # if q1_path is not None:
        #     print(f"Query 1 Path Graph: {len(q1_path)} triples")

        # print("\\nTesting Query 2...")
        # q2_df, q2_path = execute_sparql_query(combined_graph, QUERY_2_BODY)
        # if q2_df is not None:
        #     print("Query 2 Results:")
        #     print(q2_df.head())
        # if q2_path is not None:
        #     print(f"Query 2 Path Graph: {len(q2_path)} triples")
        #     # print(q2_path.serialize(format='turtle'))

        # print("\\nTesting Query 3...")
        # q3_df, q3_path = execute_sparql_query(combined_graph, QUERY_3_BODY)
        # if q3_df is not None:
        #     print("Query 3 Results:")
        #     print(q3_df.head())
        # if q3_path is not None:
        #     print(f"Query 3 Path Graph: {len(q3_path)} triples")

        # print("\\nTesting Query 4...")
        # q4_df, q4_path = execute_sparql_query(combined_graph, QUERY_4_BODY)
        # if q4_df is not None:
        #     print("Query 4 Results:")
        #     print(q4_df.head())
        # if q4_path is not None:
        #     print(f"Query 4 Path Graph: {len(q4_path)} triples")


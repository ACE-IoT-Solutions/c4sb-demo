from pathlib import Path
from rdflib import Graph
from pyshacl import validate

# Define project root to construct absolute paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Define paths for data graphs
BRICK_DATA_FILE: Path = PROJECT_ROOT / "data" / "brick-building-simple.ttl"
REC_DATA_FILE: Path = PROJECT_ROOT / "data" / "rec-building-simple.ttl"
ASHRAE_DATA_FILE: Path = PROJECT_ROOT / "data" / "ashrae-223-rtu.ttl"

# Define paths for SHACL shape graphs
BRICK_SHACL_FILE: Path = PROJECT_ROOT / "data" / "validations" / "brick" / "brick-shacl.ttl"
REC_SHACL_FILE: Path = PROJECT_ROOT / "data" / "validations" / "rec" / "rec.ttl"
# ASHRAE_SHACL_FILE = PROJECT_ROOT / "data" / "validations" / "ashrae-223" / "223p.ttl" # Old file
ASHRAE_DATA_SHAPES_FILE: Path = PROJECT_ROOT / "data" / "validations" / "ashrae-223" / "data.shapes.ttl"
ASHRAE_MODEL_SHAPES_FILE: Path = PROJECT_ROOT / "data" / "validations" / "ashrae-223" / "model.shapes.ttl"
ASHRAE_SCHEMA_SHAPES_FILE: Path = PROJECT_ROOT / "data" / "validations" / "ashrae-223" / "schema.shapes.ttl"

def validate_graph_fragment(data_graph_path, shacl_graph_paths, graph_name): # Modified to accept a list of SHACL paths
    """
    Validates a data graph against one or more SHACL shapes graphs.

    Args:
        data_graph_path (Path): Path to the data graph file.
        shacl_graph_paths (list[Path]): List of paths to the SHACL shapes graph files.
        graph_name (str): Name of the graph for display purposes.
    """
    print(f"--- Validating {graph_name} ---")
    if not data_graph_path.exists():
        print(f"ERROR: Data graph file not found: {data_graph_path}")
        print("-" * 30 + "\n")
        return
    
    combined_shacl_graph = Graph()
    all_shacl_files_found = True
    for shacl_path in shacl_graph_paths:
        if not shacl_path.exists():
            print(f"ERROR: SHACL graph file not found: {shacl_path}")
            all_shacl_files_found = False
        else:
            print(f"Loading SHACL graph: {shacl_path}")
            try:
                combined_shacl_graph.parse(str(shacl_path), format="turtle")
            except Exception as e:
                print(f"Error loading SHACL graph {shacl_path}: {e}")
                all_shacl_files_found = False # Treat loading error as file not found for simplicity
    
    if not all_shacl_files_found:
        print("One or more SHACL files could not be loaded. Aborting validation for this graph.")
        print("-" * 30 + "\n")
        return

    print(f"Data graph: {data_graph_path}")
    # print(f"SHACL graph(s): {[str(p) for p in shacl_graph_paths]}") # Already printed above

    try:
        data_graph = Graph().parse(str(data_graph_path), format="turtle")
        # shacl_graph is now combined_shacl_graph
    except Exception as e:
        print(f"Error loading graphs for {graph_name}: {e}")
        print("-" * 30 + "\n")
        return

    try:
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=combined_shacl_graph, # Use the combined graph
            ont_graph=None,  # pyshacl will load owl:imports from shacl_graph if present
            inference='rdfs', 
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
            meta_shacl=False,
            advanced=True,
            js=False,
            debug=False
        )

        print(f"Conforms: {conforms}")
        if not conforms:
            print("Validation Results:")
            # For detailed Turtle output of violations, uncomment below:
            # results_graph.serialize(destination=sys.stdout, format="turtle")
            print(results_text)
        else:
            print(f"{graph_name} is valid according to the SHACL shapes.")
        
    except Exception as e:
        print(f"Error during validation for {graph_name}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("-" * 30 + "\n")

def main():
    """
    Main function to validate graph fragments against SHACL shapes.
    """
    print("Starting SHACL validation of graph fragments...\n")

    validate_graph_fragment(BRICK_DATA_FILE, [BRICK_SHACL_FILE], "Brick Model (brick-building-simple.ttl)")
    validate_graph_fragment(REC_DATA_FILE, [REC_SHACL_FILE], "RealEstateCore Model (rec-building-simple.ttl)")
    
    ashrae_shacl_files = [
        ASHRAE_DATA_SHAPES_FILE,
        ASHRAE_MODEL_SHAPES_FILE,
        ASHRAE_SCHEMA_SHAPES_FILE
    ]
    validate_graph_fragment(ASHRAE_DATA_FILE, ashrae_shacl_files, "ASHRAE 223 Model (ashrae-223-rtu.ttl)")

    print("SHACL validation process complete.")

if __name__ == "__main__":
    main()
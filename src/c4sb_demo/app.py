import streamlit as st
import rdflib # Still needed for BNode, URIRef in get_node_label
from pyvis.network import Network
import streamlit.components.v1 as components
from pathlib import Path
import tempfile
import pandas as pd # execute_sparql_query returns a DataFrame

# Import from graph_operations module using relative import
from c4sb_demo.graph_operations import (
    load_graph,
    create_combined_linked_graph,
    execute_sparql_query,
    QUERY_1_BODY,
    QUERY_2_BODY,
    QUERY_3_BODY,
    QUERY_4_BODY
)
from c4sb_demo.sparql_constants import (
    RDFS_LABEL,      # Used in get_node_label
    SKOS_PREF_LABEL,   # Used in get_node_label
)

# Helper function to get a display label for a node (uses RDFS_LABEL, SKOS_PREFLABEL from graph_operations)
def get_node_label(graph, node):
    label = None
    # Try RDFS.label
    for _, _, o_literal in graph.triples((node, RDFS_LABEL, None)):
        label = str(o_literal)
        break
    if not label:
        # Try SKOS.prefLabel
        for _, _, o_literal in graph.triples((node, SKOS_PREF_LABEL, None)):
            label = str(o_literal)
            break
    if not label:
        # Fallback for URIs and BNodes
        if isinstance(node, rdflib.BNode): # Blank node
            label = f"_:{str(node)}" 
        elif isinstance(node, rdflib.URIRef): # URI
            label = str(node).split('#')[-1].split('/')[-1]
            if not label and str(node).startswith("http"): 
                label = str(node)
        else: # Literal or other
            label = str(node)
    return label

# Helper function to display a graph 
def display_graph_info(graph, title, key_suffix=""):
    if graph is None or len(graph) == 0:
        st.write(f"{title}: Graph is empty or failed to load.")
        return

    st.subheader(title)
    st.text(f"Number of triples: {len(graph)}")
    
    if st.checkbox(f"Show Turtle RDF for {title}", key=f"show_rdf_{key_suffix}"):
        st.text_area("Turtle RDF", graph.serialize(format="turtle"), height=200, key=f"rdf_{key_suffix}")

    if st.checkbox(f"Visualize {title} with Pyvis", key=f"show_pyvis_{key_suffix}"):
        try:
            net = Network(notebook=True, height="750px", width="100%", cdn_resources='remote', directed=True)
            net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)
            
            # Keep track of rdflib nodes already added to Pyvis to use their string representation as ID
            # and their computed label for display.
            # Pyvis nodes are added using their string representation as ID.
            processed_nodes = {} # Maps rdflib node to its string ID used in Pyvis

            for s, p, o in graph:
                s_str_id = str(s)
                if s not in processed_nodes:
                    label_s = get_node_label(graph, s)
                    net.add_node(s_str_id, label=label_s, title=str(s))
                    processed_nodes[s] = s_str_id
                
                if isinstance(o, rdflib.URIRef) or isinstance(o, rdflib.BNode):
                    o_str_id = str(o)
                    if o not in processed_nodes:
                        label_o = get_node_label(graph, o)
                        net.add_node(o_str_id, label=label_o, title=str(o))
                        processed_nodes[o] = o_str_id
                    
                    edge_label = get_node_label(graph, p)
                    net.add_edge(s_str_id, o_str_id, label=edge_label, title=str(p))
                else: # o is a literal
                    prop_label = get_node_label(graph, p)
                    # Literals are added to the title of the subject node in Pyvis
                    # Retrieve the node from Pyvis; net.get_node() expects the node ID (string)
                    pyvis_node = net.get_node(s_str_id) 
                    if pyvis_node:
                        current_title = pyvis_node.get('title', str(s))
                        if not isinstance(current_title, str):
                            current_title = str(current_title)
                        new_prop_info = f"\n{prop_label}: {str(o)}"
                        # Update the title in the Pyvis node object directly
                        if new_prop_info not in current_title:
                            pyvis_node['title'] = current_title + new_prop_info
                    # else: st.warning(f"Node {s_str_id} not found in Pyvis for literal.")

            if not net.nodes:
                st.write("Graph has no nodes to visualize with Pyvis.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp_file:
                net.save_graph(tmp_file.name)
                html_file_path = tmp_file.name
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                components.html(source_code, height=800, scrolling=True)
            
            Path(html_file_path).unlink(missing_ok=True)

        except Exception as e:
            st.error(f"Error visualizing graph {title} with Pyvis: {e}")
            import traceback
            st.error(traceback.format_exc())

def run():
    st.set_page_config(layout="wide")
    st.title("Digital Twin Graph Explorer")

    # Initialize session state variables if they don't exist
    # Using dict syntax for session_state
    if 'g_brick' not in st.session_state:
        st.session_state['g_brick'] = None
    if 'g_rec' not in st.session_state:
        st.session_state['g_rec'] = None
    if 'g_ashrae' not in st.session_state:
        st.session_state['g_ashrae'] = None
    if 'g_combined_linked' not in st.session_state:
        st.session_state['g_combined_linked'] = None
    if 'show_combined_graph_and_queries' not in st.session_state:
        st.session_state['show_combined_graph_and_queries'] = False

    # Initialize session state for query results and paths using dictionary syntax
    if 'query1_results_df' not in st.session_state:
        st.session_state['query1_results_df'] = None
    if 'query1_path_graph' not in st.session_state:
        st.session_state['query1_path_graph'] = None
    if 'query2_results_df' not in st.session_state:
        st.session_state['query2_results_df'] = None
    if 'query2_path_graph' not in st.session_state:
        st.session_state['query2_path_graph'] = None
    if 'query3_results_df' not in st.session_state:
        st.session_state['query3_results_df'] = None
    if 'query3_path_graph' not in st.session_state:
        st.session_state['query3_path_graph'] = None
    if 'query4_results_df' not in st.session_state:
        st.session_state['query4_results_df'] = None
    if 'query4_path_graph' not in st.session_state:
        st.session_state['query4_path_graph'] = None

    project_root = Path(__file__).resolve().parent.parent.parent # cs4b-demo
    data_path = project_root / "data"
    brick_file = data_path / "brick-building-simple.ttl"
    rec_file = data_path / "rec-building-simple.ttl"
    ashrae_file = data_path / "ashrae-223-rtu.ttl"

    # Load individual graphs if not already loaded, using imported load_graph
    if st.session_state['g_brick'] is None:
        st.session_state['g_brick'] = load_graph(brick_file)
    if st.session_state['g_rec'] is None:
        st.session_state['g_rec'] = load_graph(rec_file)
    if st.session_state['g_ashrae'] is None:
        st.session_state['g_ashrae'] = load_graph(ashrae_file)
    
    g_brick = st.session_state['g_brick']
    g_rec = st.session_state['g_rec']
    g_ashrae = st.session_state['g_ashrae']

    link_button_pressed = st.button("Link Graphs and Show Combined Queries")

    if link_button_pressed:
        st.session_state['show_combined_graph_and_queries'] = True
        if brick_file.exists() and rec_file.exists() and ashrae_file.exists():
            st.session_state['g_combined_linked'] = create_combined_linked_graph(
                brick_file=brick_file, 
                rec_file=rec_file, 
                ashrae_file=ashrae_file
            )
            if st.session_state['g_combined_linked'] is None:
                st.error("Failed to create and link graphs. Check logs/console for errors from graph_operations.")
                st.session_state['show_combined_graph_and_queries'] = False
            else:
                st.success("Graphs linked successfully using graph_operations module!")
        else:
            st.error("One or more data files are missing. Cannot link graphs.")
            st.session_state['show_combined_graph_and_queries'] = False
            
    g_combined_linked = st.session_state['g_combined_linked']

    if st.session_state['show_combined_graph_and_queries'] and g_combined_linked is not None:
        st.subheader("Combined and Linked Graph")
        if len(g_combined_linked) > 0:
            st.text(f"Number of triples in combined graph: {len(g_combined_linked)}")
            display_graph_info(g_combined_linked, "Combined and Linked Graph Visualization", key_suffix="combined_linked")
        else:
            st.warning("Combined graph is empty. This might happen if linking failed or source graphs are empty.")

        st.subheader("SPARQL Queries on Combined Graph")

        # Query 1 - Use imported QUERY_1_BODY
        st.text_area("Query 1: ASHRAE Components for Brick RTU", QUERY_1_BODY, height=200, key="q1_text_area")
        if st.button("Run Query 1", key="q1_run_button"):
            try:
                results_df, path_graph = execute_sparql_query(g_combined_linked, QUERY_1_BODY)
                st.session_state['query1_results_df'] = results_df
                st.session_state['query1_path_graph'] = path_graph
                if results_df is None: # Check if execute_sparql_query itself returned None for df
                    st.error("Query 1 execution failed to produce tabular results (returned None).")
            except Exception as e:
                st.error(f"Error running Query 1: {e}")
                st.text_area("Query body (error context):", QUERY_1_BODY, height=100, key="q1_error_query_body")
                st.session_state['query1_results_df'] = None 
                st.session_state['query1_path_graph'] = None

        # Display Query 1 results if available in session state
        query1_results_df = st.session_state.get('query1_results_df')
        query1_path_graph = st.session_state.get('query1_path_graph')

        if query1_results_df is not None:
            if not query1_results_df.empty:
                st.subheader("Query 1 Results")
                st.dataframe(query1_results_df)
            # Check if it's an empty DataFrame (e.g. from a query with no results, not an execution error)
            elif isinstance(query1_results_df, pd.DataFrame) and query1_results_df.empty:
                st.warning("Query 1 returned no tabular results.")
            # No specific message if results_df is None here, as it's handled after button press
            
            if query1_path_graph is not None:
                # Check if path_graph is an rdflib.Graph and has triples
                if isinstance(query1_path_graph, rdflib.Graph) and len(query1_path_graph) > 0:
                    st.subheader("Query 1 Path Visualization")
                    display_graph_info(query1_path_graph, "Graph for Query 1 Path", key_suffix="query1_path")
                elif isinstance(query1_path_graph, rdflib.Graph):
                    st.info("The path graph for Query 1 is empty or contains no triples.")
                # else: path_graph might be None or not a graph, handled by not displaying
        
        # Query 2 - Use imported QUERY_2_BODY
        st.text_area("Query 2: Brick Sensor Context with REC Links", QUERY_2_BODY, height=250, key="q2_text_area")
        if st.button("Run Query 2", key="q2_run_button"):
            try:
                results_df, path_graph = execute_sparql_query(g_combined_linked, QUERY_2_BODY)
                st.session_state['query2_results_df'] = results_df
                st.session_state['query2_path_graph'] = path_graph
                if results_df is None:
                    st.error("Query 2 execution failed to produce tabular results (returned None).")
            except Exception as e:
                st.error(f"Error running Query 2: {e}")
                st.text_area("Query body (error context):", QUERY_2_BODY, height=100, key="q2_error_query_body")
                st.session_state['query2_results_df'] = None
                st.session_state['query2_path_graph'] = None

        # Display Query 2 results if available in session state
        query2_results_df = st.session_state.get('query2_results_df')
        query2_path_graph = st.session_state.get('query2_path_graph')

        if query2_results_df is not None:
            if not query2_results_df.empty:
                st.subheader("Query 2 Results")
                st.dataframe(query2_results_df)
            elif isinstance(query2_results_df, pd.DataFrame) and query2_results_df.empty:
                st.warning("Query 2 returned no tabular results.")

            if query2_path_graph is not None:
                if isinstance(query2_path_graph, rdflib.Graph) and len(query2_path_graph) > 0:
                    st.subheader("Query 2 Path Visualization")
                    display_graph_info(query2_path_graph, "Graph for Query 2 Path", key_suffix="query2_path")
                elif isinstance(query2_path_graph, rdflib.Graph):
                    st.info("The path graph for Query 2 is empty or contains no triples.")

        # Query 3 - Use imported QUERY_3_BODY
        st.text_area("Query 3: ASHRAE Compressor, Linked Brick RTU, and REC Room Area", QUERY_3_BODY, height=250, key="q3_text_area")
        if st.button("Run Query 3", key="q3_run_button"):
            try:
                results_df, path_graph = execute_sparql_query(g_combined_linked, QUERY_3_BODY)
                st.session_state['query3_results_df'] = results_df
                st.session_state['query3_path_graph'] = path_graph
                if results_df is None:
                    st.error("Query 3 execution failed to produce tabular results (returned None).")
            except Exception as e:
                st.error(f"Error running Query 3: {e}")
                st.text_area("Query body (error context):", QUERY_3_BODY, height=100, key="q3_error_query_body")
                st.session_state['query3_results_df'] = None
                st.session_state['query3_path_graph'] = None
        
        # Display Query 3 results if available in session state
        query3_results_df = st.session_state.get('query3_results_df')
        query3_path_graph = st.session_state.get('query3_path_graph')

        if query3_results_df is not None:
            if not query3_results_df.empty:
                st.subheader("Query 3 Results")
                st.dataframe(query3_results_df)
            elif isinstance(query3_results_df, pd.DataFrame) and query3_results_df.empty:
                st.warning("Query 3 returned no tabular results.")
            
            if query3_path_graph is not None:
                if isinstance(query3_path_graph, rdflib.Graph) and len(query3_path_graph) > 0:
                    st.subheader("Query 3 Path Visualization")
                    display_graph_info(query3_path_graph, "Graph for Query 3 Path", key_suffix="query3_path")
                elif isinstance(query3_path_graph, rdflib.Graph):
                    st.info("The path graph for Query 3 is empty or contains no triples.")

        # Query 4 - New Query for HVAC Voltage
        st.text_area("Query 4: HVAC Unit Voltage for ex:room_101", QUERY_4_BODY, height=250, key="q4_text_area")
        if st.button("Run Query 4", key="q4_run_button"):
            try:
                results_df, path_graph = execute_sparql_query(g_combined_linked, QUERY_4_BODY)
                st.session_state['query4_results_df'] = results_df
                st.session_state['query4_path_graph'] = path_graph
                if results_df is None:
                    st.error("Query 4 execution failed to produce tabular results (returned None).")
            except Exception as e:
                st.error(f"Error running Query 4: {e}")
                st.text_area("Query body (error context):", QUERY_4_BODY, height=100, key="q4_error_query_body")
                st.session_state['query4_results_df'] = None
                st.session_state['query4_path_graph'] = None
        
        # Display Query 4 results if available in session state
        query4_results_df = st.session_state.get('query4_results_df')
        query4_path_graph = st.session_state.get('query4_path_graph')

        if query4_results_df is not None:
            if not query4_results_df.empty:
                st.subheader("Query 4 Results")
                st.dataframe(query4_results_df)
            elif isinstance(query4_results_df, pd.DataFrame) and query4_results_df.empty:
                st.warning("Query 4 returned no tabular results.")
            
            if query4_path_graph is not None:
                if isinstance(query4_path_graph, rdflib.Graph) and len(query4_path_graph) > 0:
                    st.subheader("Query 4 Path Visualization")
                    display_graph_info(query4_path_graph, "Graph for Query 4 Path", key_suffix="query4_path")
                elif isinstance(query4_path_graph, rdflib.Graph):
                    st.info("The path graph for Query 4 is empty or contains no triples.")

    st.header("Individual Graph Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        if g_brick:
            display_graph_info(g_brick, "Brick Data", key_suffix="brick")
        else:
            st.warning("Brick graph not loaded.")
    with col2:
        if g_rec:
            display_graph_info(g_rec, "RealEstateCore Data", key_suffix="rec")
        else:
            st.warning("RealEstateCore graph not loaded.")
    with col3:
        if g_ashrae:
            display_graph_info(g_ashrae, "ASHRAE 223 Data", key_suffix="ashrae")
        else:
            st.warning("ASHRAE 223 graph not loaded.")

if __name__ == "__main__":
    run()

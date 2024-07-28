import graphistry
from py2neo import Graph

def plot_graph(query: str):
    # Initialize Graphistry with your API key
    graphistry.register(api=3, protocol='https', server='hub.graphistry.com', username='YOUR_USERNAME', password='YOUR_PASSWORD')

    # Connect to Neo4j and run the query
    graph = Graph(
        os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "test"))
    )
    results = graph.run(query).data()

    # Process the results to get nodes and edges
    nodes = []
    edges = []
    for record in results:
        n1, r, n2 = record['n1'], record['r1'], record['n2']
        nodes.append(n1)
        nodes.append(n2)
        edges.append(r)

    # Create a dataframe for nodes and edges
    nodes_df = pd.DataFrame(nodes)
    edges_df = pd.DataFrame(edges)

    # Plot using Graphistry
    return graphistry.bind(source='start', destination='end', node='name').edges(edges_df).nodes(nodes_df).plot()


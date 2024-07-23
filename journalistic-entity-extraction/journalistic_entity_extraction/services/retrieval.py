from py2neo import Graph

def retrieve_relevant_information(graph: Graph, query: str):
    cypher_query = """
    MATCH (n)
    WHERE n.name CONTAINS 
    RETURN n
    """
    results = graph.run(cypher_query, query=query).data()
    return results

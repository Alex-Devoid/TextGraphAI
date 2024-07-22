from py2neo import Graph, Node, Relationship

def build_knowledge_graph(graph: Graph, entities):
    for entity in entities:
        node = Node(entity['type'], name=entity['text'])
        graph.merge(node, entity['type'], 'name')
    return "Knowledge graph updated"

from numbers import Number


class SankeyEdge:
    def __init__(self, source: int, target: int,
                 value: Number, label: str = ""):
        self.source_id = source
        self.target_id = target
        self.value = value
        self.label = label


class SankeyGraph:
    def __init__(self):
        self.node_names = []
        self.node_ids = dict()
        self.edges = []

    def add_node(self, name: str):
        if name not in self.node_ids.keys():
            self.node_ids[name] = len(self.node_names)
            self.node_names.append(name)
        return self.node_ids[name]

    # def find_node(self, name: str):
    #     return self.nodes[name]

    def add_edge(self, source: str, target: str, value: Number,
                 label: str = ""):
        source_id = self.add_node(source)
        target_id = self.add_node(target)
        self.edges.append(SankeyEdge(
            source_id, target_id, value, label
        ))

    def get_edge_sources(self):
        return [e.source_id for e in self.edges]

    def get_edge_targets(self):
        return [e.target_id for e in self.edges]

    def get_edge_values(self):
        return [e.value for e in self.edges]

    def get_edge_labels(self):
        return [e.label for e in self.edges]

    def get_node_labels(self):
        return self.node_names

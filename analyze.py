from sys import argv
import sqlite3 as sql
from numbers import Number

from plotly.graph_objects import Figure, Sankey

MAPPINGS = {
    "Essen": {
        "Empfaenger": ["edeka", "rewe", "frittenwerk", "gastro",
                       "merzenich", "mcdonalds", "mensa", "backwerk", "subway"]
    },
    "Sparkonto": {"Empfaenger": ["kleingeld"]},
    "Bargeld": {"Empfaenger": ["bargeld"]},
    "Telefon": {"Empfaenger": ["congstar"]},
    "Auto": {
        "Empfaenger": ["aral", "a.t.u"],
        "Verwendungszweck": ["kfz-steuer"]
    },
    "Gesundheit": {"Empfaenger": ["barmer"]},
}

FILTER = [
    [("Sender", "martin lehmann"), ("Verwendungszweck", "studium plus")],
    [("Sender", "henning lehmann")],
    [("Empfaenger", "henning lehmann")],
]

# class SankeyNode:
#     def __init__(self, label: str, id: int):
#         self.label = label
#         self.id = id


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

    # def print_nodes(self):
    #


def select(month, year):
    con = sql.connect("transaktionen.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    res = cur.execute("""
        select * from Umsaetze where
            strftime('%Y', Wertstellungsdatum) = ? and
            strftime('%m', Wertstellungsdatum) = ?;""", (year, month))
    lines = res.fetchall()

    # ein = 0
    # aus = 0
    # for line in lines:
    #     if line[1]:
    #         ein += line[0]
    #     else:
    #         aus += line[0]

    # print(f"{year} {month}: Einnahmen {ein/100}, Ausgaben {aus/100}")
    con.close()

    return [dict(t) for t in lines]


def match_filter(filter, transaction):
    for k, v in filter:
        if transaction[k].lower().find(v) == -1:
            return False
    return True


def match_any_filter(transaction):
    for f in FILTER:
        if match_filter(f, transaction):
            print(f"Filtered: {transaction['Sender']} --{transaction['Betrag'] / 100}-> {
                  transaction['Empfaenger']} ({transaction['Verwendungszweck']})")
            return True
    return False


def match_category(transaction):
    for category, map in MAPPINGS.items():
        for field, terms in map.items():
            for term in terms:
                if transaction[field].lower().find(term) != -1:
                    return category
    return "Rest"


def viz(transactions):
    transactions = [t for t in transactions if not match_any_filter(t)]

    einnahmen = [t for t in transactions if t["Einnahme"]]
    # einnahmen = [t for t in einnahmen if not match_any_filter(t)]
    ausgaben = [t for t in transactions if not t["Einnahme"]]

    # sum_ein = sum([t["Betrag"] for t in einnahmen])
    # sum_aus = -sum([t["Betrag"] for t in ausgaben])
    # diff = sum_ein - sum_aus

    for lnk_target in ausgaben:
        lnk_target["category"] = match_category(lnk_target)

    g = SankeyGraph()

    for trans in einnahmen:
        g.add_edge(trans["Sender"], "Girokonto",
                   trans["Betrag"] / 100,
                   label=f"{trans["Sender"]} - {trans["Verwendungszweck"]}")
        # print(f"{trans['Sender']} --{trans['Betrag'] / 100}-> Girokonto ({trans['Verwendungszweck']})")

    for trans in ausgaben:
        g.add_edge("Girokonto", trans["category"],
                   -trans["Betrag"] / 100,
                   label=f"{trans["Empfaenger"]} - {trans["Verwendungszweck"]}")

    # print(g.get_node_labels())
    # print(g.get_edge_sources())
    # print(g.get_edge_targets())

    fig = Figure(
        data=Sankey(
            node={"label": g.get_node_labels()},
            link={
                "source": g.get_edge_sources(), "target": g.get_edge_targets(),
                "value": g.get_edge_values(), "label": g.get_edge_labels()
            }
        )
    )
    fig.update_layout(title_text="Die Nanzen")
    fig.show()


def main(argv):
    trans = select("11", "2025")
    viz(trans)
    # for y in [2025, 2026]:
    #     for m in range(1, 13):
    #         select(f"{m:02}", str(y))


if __name__ == "__main__":
    main(argv)

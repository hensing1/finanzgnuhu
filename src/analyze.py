from sys import argv
from numbers import Number
import locale

from dash import Dash, html, dcc
from plotly import graph_objects as go

MAPPINGS = {
    "Essen": {
        "Empfaenger": ["edeka", "rewe", "frittenwerk", "gastro",
                       "merzenich", "mcdonalds", "mensa", "backwerk", "subway", "foodamigos"]
    },
    "Sparkonto": {"Empfaenger": ["kleingeld"]},
    "Bargeld": {"Empfaenger": ["bargeld"]},
    "Telefon": {"Empfaenger": ["congstar"]},
    "Auto": {
        "Empfaenger": ["aral", "a.t.u"],
        "Verwendungszweck": ["kfz-steuer"]
    },
    "Gesundheit": {"Empfaenger": ["barmer", "apotheke"]},
}

FILTER = [
    [("Sender", "martin lehmann"), ("Verwendungszweck", "studium plus")],
    [("Sender", "henning lehmann")],
    [("Empfaenger", "henning lehmann")],
]

MONTHS = ["Nulluar", "Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]

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


def make_sankey(transactions):
    einnahmen = [t for t in transactions if t["Einnahme"]]
    ausgaben = [t for t in transactions if not t["Einnahme"]]

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
                   abs(trans["Betrag"] / 100),
                   label=f"{trans["Empfaenger"]} - {trans["Verwendungszweck"]}")

    return go.Sankey(
        node={"label": g.get_node_labels()},
        link={
            "source": g.get_edge_sources(), "target": g.get_edge_targets(),
            "value": g.get_edge_values(), "label": g.get_edge_labels()
        }
    )


def ein_aus(transactions):
    sum_ein = sum([t['Betrag'] for t in transactions if t['Einnahme']])
    sum_aus = sum([abs(t['Betrag']) for t in transactions if not t['Einnahme']])
    return sum_ein, sum_aus


def main(argv):
    locale.setlocale(locale.LC_ALL, '')
    ts = select_all()
    ts = [t for t in ts if not match_any_filter(t)]

    content = [html.H1("Die Nanzen")]

    for y, m in [(2026, 2), (2026, 1), (2025, 12), (2025, 11), (2025, 10), (2025, 9),
                 (2025, 8), (2025, 7), (2025, 6), (2025, 5), (2025, 4),
                 (2025, 3), (2025, 2)]:
        content.append(html.H2(f"{MONTHS[m]} {y}"))
        transactions = [t for t in ts
                        if t['Wertstellungsdatum'].year == y and t['Wertstellungsdatum'].month == m]
        sankey = make_sankey(transactions)
        content.append(dcc.Graph(figure=go.Figure(sankey)))

        ein, aus = ein_aus(transactions)
        content.append(html.P(f"Einnahmen: {locale.format_string('%.2f', ein / 100, grouping=True)}€, "
                              f"Ausgaben: {locale.format_string('%.2f', aus / 100, grouping=True)}€"))

    app = Dash("Die Nanzen")

    app.layout = html.Div(content)

    app.run(debug=True)


if __name__ == "__main__":
    main(argv)

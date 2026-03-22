import src.db_connector as db_connector
from src.sankey import SankeyGraph

from dash import dcc, callback, Input, Output
from dash.exceptions import PreventUpdate
from plotly import graph_objects as go


def make_sankey(transactions):
    einnahmen = [t for t in transactions if t["Einnahme"] and not t["ignorieren"]]
    ausgaben = [t for t in transactions if not t["Einnahme"] and not t["ignorieren"]]

    g = SankeyGraph()

    # Sender -> Girokonto
    for trans in einnahmen:
        g.add_edge(trans["Sender"], "Girokonto",
                   trans["Betrag"] / 100,
                   label=f"{trans["Sender"]} - {trans["Verwendungszweck"]}")
        # print(f"{trans['Sender']} --{trans['Betrag'] / 100}-> Girokonto ({trans['Verwendungszweck']})")

    # Girokonto -> Empfänger
    for trans in ausgaben:
        g.add_edge("Girokonto", trans["KategorieName"],
                   abs(trans["Betrag"] / 100),
                   label=f"{trans["Empfaenger"]} - {trans["Verwendungszweck"]}")

    return go.Sankey(
        node={"label": g.get_node_labels()},
        link={
            "source": g.get_edge_sources(), "target": g.get_edge_targets(),
            "value": g.get_edge_values(), "label": g.get_edge_labels()
        }
    )


@callback(
    Output("sankey_graph", "figure"),
    Input("sankey_range", "start_date"),
    Input("sankey_range", "end_date"),
    Input("save_button", "n_clicks")
)
def update_sankey(start_date, end_date, _):
    if (start_date is None or end_date is None):
        raise PreventUpdate
    transactions = db_connector.select_transactions_as_view(start_date, end_date)
    sankey = make_sankey(transactions)
    return go.Figure(sankey)


def create_analyzer():
    return dcc.Graph(id="sankey_graph")

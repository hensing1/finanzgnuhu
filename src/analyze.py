import src.db_connector as db_connector
from src.sankey import SankeyGraph

from dash import dcc, callback, Input, Output, html
from dash.exceptions import PreventUpdate
from plotly import graph_objects as go


def make_sankey(einnahmen, ausgaben):

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


def make_summary(einnahmen, ausgaben):
    sum_ein = sum([t["Betrag"] for t in einnahmen]) / 100
    sum_aus = abs(sum([t["Betrag"] for t in ausgaben])) / 100
    return [
        html.P(f"Einnahmen: {sum_ein}€", style={"width": "400px"}),
        html.P(f"{round(sum_ein - sum_aus, 2)}€",
               style={"color": ("green" if sum_ein > sum_aus else "red")}),
        html.P(f"Ausgaben: {sum_aus}€", style={"width": "400px"}),
    ]


@callback(
    Output("sankey_graph", "figure"),
    Output("summary_div", "children"),
    Input("sankey_range", "start_date"),
    Input("sankey_range", "end_date"),
    Input("tabs", "value"),
    Input("save_button", "n_clicks"),
)
def update_sankey(start_date, end_date, value, _):
    if (start_date is None or end_date is None or value != "tab-1"):
        raise PreventUpdate

    transactions = db_connector.select_transactions_as_view(start_date, end_date)

    einnahmen = [t for t in transactions if t["Einnahme"] and not t["ignorieren"]]
    ausgaben = [t for t in transactions if not t["Einnahme"] and not t["ignorieren"]]
    sankey = make_sankey(einnahmen, ausgaben)
    summary = make_summary(einnahmen, ausgaben)
    return go.Figure(sankey), summary


def create_analyzer():
    return html.Div([
        html.Div(id="summary_div",
                 style={"display": "flex", "justifyContent": "space-around",
                        "textAlign": "center"}),
        dcc.Graph(id="sankey_graph")
    ])

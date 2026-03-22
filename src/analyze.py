import src.db_connector as db_connector
from src.sankey import SankeyGraph

from datetime import date, timedelta

from dash import dcc, callback, Input, Output, State
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


@callback(
    Output("sankey_range", "start_date"),
    Output("sankey_range", "end_date"),
    Input("month_prev", "n_clicks"),
    State("sankey_range", "start_date"),
    State("sankey_range", "end_date"),
    prevent_initial_call=True
)
def prev_month(_, start_date, end_date):
    start_date = date.strptime(start_date, "%Y-%m-%d")
    end_date = date.strptime(end_date, "%Y-%m-%d")
    earliest = db_connector.select_earliest_date()

    new_start = max(start_date - timedelta(days=30), earliest)
    new_end = end_date - (start_date - new_start)
    return new_start, new_end


@callback(
    Output("sankey_range", "start_date", allow_duplicate=True),
    Output("sankey_range", "end_date", allow_duplicate=True),
    Input("month_next", "n_clicks"),
    State("sankey_range", "start_date"),
    State("sankey_range", "end_date"),
    prevent_initial_call=True
)
def next_month(_, start_date, end_date):
    start_date = date.strptime(start_date, "%Y-%m-%d")
    end_date = date.strptime(end_date, "%Y-%m-%d")
    latest = db_connector.select_latest_date()

    new_end = min(end_date + timedelta(days=30), latest)
    new_start = start_date + (new_end - end_date)
    return new_start, new_end


def create_analyzer():
    return dcc.Graph(id="sankey_graph")

import src.db_connector as db_connector
from src.sankey import SankeyGraph

from dash import dcc, callback, Input, Output, html
from dash.exceptions import PreventUpdate
from plotly import graph_objects as go

import locale


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
        arrangement="snap",
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
        html.P(f"Einnahmen: {locale.currency(sum_ein, grouping=True)}",
               style={"width": "400px"}),
        html.P(f"{locale.currency(sum_ein - sum_aus, grouping=True)}",
               style={"color": ("green" if sum_ein > sum_aus else "red")}),
        html.P(f"Ausgaben: {locale.currency(sum_aus, grouping=True)}",
               style={"width": "400px"}),
    ]


@callback(
    Output("sankey_graph", "figure"),
    Output("summary_div", "children"),
    Input("acc_dropdown", "value"),
    Input("sankey_range", "start_date"),
    Input("sankey_range", "end_date"),
    Input("tabs", "value"),
    Input("insert_ok_modal", "is_open"),  # trigger when insert of new transactions is complete
    Input("save_button", "n_clicks"),
)
def update_sankey(iban, start_date, end_date, tab, insert_popup, _):
    if (start_date is None or end_date is None or tab != "tab-1" or insert_popup):
        raise PreventUpdate

    transactions = db_connector.select_transactions_as_view(iban, start_date, end_date)

    einnahmen = [t for t in transactions if t["Einnahme"] and not t["ignorieren"]]
    ausgaben = [t for t in transactions if not t["Einnahme"] and not t["ignorieren"]]
    sankey = make_sankey(einnahmen, ausgaben)
    summary = make_summary(einnahmen, ausgaben)
    fig = go.Figure(sankey)
    fig.update_layout(font_size=13, height=700)
    return fig, summary


def create_analyzer():
    return html.Div([
        html.Div(id="summary_div",
                 style={"display": "flex", "justifyContent": "space-around",
                        "textAlign": "center"}),
        html.Div(
            [dcc.Graph(id="sankey_graph")],
            style={"height": "70vh"}
        )
    ])

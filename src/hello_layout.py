from dash import callback, Input, Output, html
from dash.exceptions import PreventUpdate

from src.db_connector import select_num_transactions
from src.parse_csv import create_csv_uploader


@callback(
    Output("success_msg", "children"),
    Input("insert_ok_modal", "is_open"),
)
def on_dialogue_close(insert_ok_is_open):
    if insert_ok_is_open or select_num_transactions() == 0:
        raise PreventUpdate

    # TODO: Das ist irgendwie kacke
    return [
        "Erste Transaktionen erfolgreich eingefügt!",
        html.Br(),
        "Bitte starte die App neu."
    ]


def create_hello_page():
    return html.Div(
        [
            html.H1("Hi, dies ist dein persönliches Finanz-Analysedings!"),
            create_csv_uploader(),
            html.P(id="success_msg")
        ],
        style={
            "height": "100vh",
            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "align-items": "center"
        }
    )

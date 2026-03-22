import locale
from datetime import timedelta

from dash import Dash, dcc, html

import src.db_connector as db_connector
from src.nanalyze import create_analyzer
from src.categorize import create_categorizer
# from src.nategorize import create_nategorizer


def make_date_picker():
    earliest = db_connector.select_earliest_date()
    latest = db_connector.select_latest_date()

    button_style = {"maxHeight": "4em"}

    return html.Div(
        [
            dcc.Button("🡨 Monat zurück", id="month_prev", style=button_style),
            html.Div(
                [dcc.DatePickerRange(
                    id="sankey_range",
                    min_date_allowed=earliest,
                    max_date_allowed=latest,
                    start_date=latest - timedelta(days=29),
                    end_date=latest
                )],
                style={
                    "maxWidth": "250px",
                    "paddingTop": "20px",
                    "paddingBottom": "20px"
                }
            ),
            dcc.Button("Monat weiter 🡪", id="month_next", style=button_style),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-evenly",
            "alignItems": "baseline",
        }
    )


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash("Die Nanzen")
    app.layout = html.Div([
        make_date_picker(),
        dcc.Tabs([
            dcc.Tab(label="Analysieren", children=[create_analyzer()]),
            dcc.Tab(label="Kategorisieren", children=[create_categorizer()]),
            # dcc.Tab(label="Kategorisieren v2", children=[create_nategorizer()])
        ])
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

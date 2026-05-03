from dash import html, dcc

from src.analyze import create_analyzer
from src.categorize import create_categorizer
from src.header import create_header


def create_standard_layout():
    return html.Div([
        create_header(),
        dcc.Tabs([
            dcc.Tab(label="Diagramm", children=[create_analyzer()]),
            dcc.Tab(label="Transaktionen", children=[create_categorizer()]),
        ], id="tabs", value="tab-1")
    ])

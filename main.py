import locale

from dash import Dash, html, dcc

from src.analyze import create_analyzer
from src.categorize import create_categorizer
from src.header import create_header


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash(__name__)  # , external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div([
        create_header(),
        dcc.Tabs([
            dcc.Tab(label="Diagramm", children=[create_analyzer()]),
            dcc.Tab(label="Transaktionen", children=[create_categorizer()]),
        ], id="tabs", value="tab-1")
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

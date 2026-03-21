import locale

from dash import Dash, dcc, html

from src.categorize import create_categorizer
from src.nanalyze import create_analyzer


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash("Die Nanzen")
    app.layout = html.Div([
        dcc.Tabs([
            dcc.Tab(label="Analysieren", children=[create_analyzer()]),
            dcc.Tab(label="Kategorisieren", children=[create_categorizer()]),
        ])
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

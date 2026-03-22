import locale

from dash import Dash, dcc, html

from src.nanalyze import create_analyzer
from src.categorize import create_categorizer
# from src.nategorize import create_nategorizer


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash("Die Nanzen")
    app.layout = html.Div([
        dcc.Tabs([
            dcc.Tab(label="Analysieren", children=[create_analyzer()]),
            dcc.Tab(label="Kategorisieren", children=[create_categorizer()]),
            # dcc.Tab(label="Kategorisieren v2", children=[create_nategorizer()])
        ])
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

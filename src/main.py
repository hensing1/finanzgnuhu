import locale

from dash import Dash, dcc, html

from categorize import create_categorizer


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash("Die Nanzen")
    app.layout = html.Div([
        dcc.Tabs([
            dcc.Tab(label="Analysieren", children=[html.Div()]),
            dcc.Tab(label="Kategorisieren", children=[create_categorizer()]),
        ])
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

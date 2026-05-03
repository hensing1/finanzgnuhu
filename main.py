import locale
from pathlib import Path

from dash import Dash

from definitions import SQLITE_FILE
from src.db_connector import select_num_transactions
from src.initialize import initialize_app


def make_layout():
    if select_num_transactions() == 0:
        from src.hello_layout import create_hello_page
        return create_hello_page()
    else:
        from src.standard_layout import create_standard_layout
        return create_standard_layout()


def main():
    locale.setlocale(locale.LC_ALL, '')
    app = Dash(__name__)  # , external_stylesheets=[dbc.themes.BOOTSTRAP])

    # check if app is run for the first time
    if not Path(SQLITE_FILE).exists():
        initialize_app()

    app.layout = make_layout

    app.run(debug=True)


if __name__ == "__main__":
    main()

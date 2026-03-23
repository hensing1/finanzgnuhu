import locale
from datetime import date, timedelta
from calendar import monthrange

from dash import Dash, dcc, html, callback, Input, Output, State

import src.db_connector as db_connector
from src.analyze import create_analyzer
from src.categorize import create_categorizer


@callback(
    Output("sankey_range", "start_date"),
    Output("sankey_range", "end_date"),
    Input("month_prev", "n_clicks"),
    State("sankey_range", "start_date"),
    prevent_initial_call=True
)
def prev_month(_, start_date):
    start_date = date.strptime(start_date, "%Y-%m-%d")
    earliest = db_connector.select_earliest_date()

    month_end_day = monthrange(start_date.year, start_date.month)[1]
    if start_date == earliest:
        new_end = date(start_date.year, start_date.month, month_end_day)
        return start_date, new_end

    month_start = date(start_date.year, start_date.month, 1)

    if start_date.day != 1:
        new_start = max(month_start, earliest)
        new_end = date(start_date.year, start_date.month, month_end_day)
        return new_start, new_end

    last_of_prev_month = month_start - timedelta(days=1)
    first_of_prev_month = date(last_of_prev_month.year, last_of_prev_month.month, 1)

    return max(first_of_prev_month, earliest), last_of_prev_month


@callback(
    Output("sankey_range", "start_date", allow_duplicate=True),
    Output("sankey_range", "end_date", allow_duplicate=True),
    Input("month_next", "n_clicks"),
    State("sankey_range", "end_date"),
    prevent_initial_call=True
)
def next_month(_, end_date):
    end_date = date.strptime(end_date, "%Y-%m-%d")
    latest = db_connector.select_latest_date()

    if end_date == latest:
        new_start = date(end_date.year, end_date.month, 1)
        return new_start, end_date

    month_end_day = monthrange(end_date.year, end_date.month)[1]
    month_end = date(end_date.year, end_date.month, month_end_day)

    if end_date.day != month_end_day:
        new_end = min(month_end, latest)
        new_start = date(new_end.year, new_end.month, 1)
        return new_start, new_end

    next_month_start = month_end + timedelta(days=1)
    next_month_end_day = monthrange(next_month_start.year, next_month_start.month)[1]
    next_month_end = date(next_month_start.year, next_month_start.month, next_month_end_day)
    new_end = min(next_month_end, latest)
    return next_month_start, new_end


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
            dcc.Tab(label="Diagramm", children=[create_analyzer()]),
            dcc.Tab(label="Kategorien", children=[create_categorizer()]),
        ], id="tabs")  # , value="tab-2")
    ])

    app.run(debug=True)


if __name__ == "__main__":
    main()

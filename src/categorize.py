import db_connector

from dash import Dash, dash_table, html, dcc, callback, Input
from dash.dash_table.Format import Format, Scheme, Group, Symbol
import locale


def transform_for_datatable(transactions):
    transactions.sort(key=lambda t: t["Wertstellungsdatum"])
    for t in transactions:
        t["Datum"] = t["Wertstellungsdatum"].strftime("%a, %d. %b")
        t["Von/An"] = t["Sender"] if t["Betrag"] > 0 else t["Empfaenger"]
        t["Betrag"] /= 100


@callback(
    Input("mybutton", "n_clicks")
)
def dings():
    global ts
    for t in ts:
        t["Verwendungszweck"] = "ohoho"
        t["Kategorie"] = 4


def main():
    global ts
    ts = db_connector.select("02", "2026", [
        "Hash", "Wertstellungsdatum", "Sender", "Empfaenger", "Verwendungszweck",
        "Betrag", "Kategorie"
    ])
    transform_for_datatable(ts)
    cats = db_connector.select_categories()

    app = Dash()
    money = Format(
        scheme=Scheme.fixed,
        precision=2,
        group=Group.yes,
        groups=3,
        group_delimiter='.',
        decimal_delimiter=',',
        symbol=Symbol.yes,
        symbol_suffix=u'€')
    app.layout = html.Div([
        dcc.Button("Hi!", id="mybutton", n_clicks=0),
        dash_table.DataTable(
        ts,
        columns=[
            {"id": "Datum", "name": "Datum"},
            {"id": "Von/An", "name": "Von/An"},
            {"id": "Verwendungszweck", "name": "Zweck"},
            {"id": "Betrag", "name": "Betrag", "type": "numeric", "format": money},
            {"id": "Kategorie", "name": "Kategorie", "presentation": "dropdown",
             "editable": True},
        ],
        style_cell={"fontWeight": "bold", "textAlign": "left", "padding": "7px"},
        style_cell_conditional=[
            {"if": {"column_id": "Betrag"}, "textAlign": "right"},
            {
                "if": {"column_id": "Verwendungszweck"},
                "maxWidth": "400px",
                "overflow": "hidden",
                "textOverflow": "ellipsis"
            }
        ],
        tooltip_data=[
            {"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in ts
        ],
        tooltip_duration=None,
        style_header={"backgroundColor": "rgb(210, 210, 210)", "fontSize": "110%"},
        style_data_conditional=[
            {
                "if": {
                    "filter_query": "{Betrag} > 0"
                },
                "color": "green"
            }
        ],
        dropdown={
            "Kategorie": {
                "options": [
                    {"label": i[1], "value": i[0]} for i in cats
                ]
            }
        }
        # style_as_list_view=True
    )])
    app.run(debug=True)


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')
    main()


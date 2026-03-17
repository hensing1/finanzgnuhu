import db_connector

from enum import Enum
import locale

from dash import Dash, dash_table, html, dcc, callback, Input, Output
from dash.dash_table.Format import Format, Scheme, Group, Symbol


MAPPINGS = {
    "Essen": {
        "Empfaenger": ["edeka", "rewe", "frittenwerk", "gastro", "netto", "king of doner",
                       "merzenich", "mcdonalds", "mensa", "backwerk", "subway", "foodamigos",
                       "burgerfaktur", "imbiss", "losteria"],
        "Verwendungszweck": ["Picnic"]
    },
    "Sparkonto": {"Empfaenger": ["kleingeld"]},
    "Bargeld": {"Empfaenger": ["bargeld"]},
    "Telefon": {"Empfaenger": ["congstar"]},
    "Auto": {
        "Empfaenger": ["aral", "a.t.u"],
        "Verwendungszweck": ["kfz-steuer"]
    },
    "Gesundheit": {"Empfaenger": ["barmer", "apotheke"]},
    "Abos": {"Verwendungszweck": ["new york times"]}
}


class CategoryStatus(Enum):
    NONE = 0
    AUTO_CATEGORIZED = 1
    USER_CATEGORIZED = 2


def match_category(transaction):
    for category, map in MAPPINGS.items():
        for field, terms in map.items():
            for term in terms:
                if transaction[field].lower().find(term) != -1:
                    return category
    return ""


@callback(
    Output("trans_table", "data"),
    [Input("cat_button", "n_clicks"), Input("trans_table", "data")],
    prevent_initial_call=False
)
def categorize(n_clicks, data):
    global CAT_IDS
    for t in data:
        t["Kategorie"] = CAT_IDS[match_category(t)]
    return data


def transform_for_datatable(transactions):
    transactions.sort(key=lambda t: t["Wertstellungsdatum"])
    for t in transactions:
        t["Datum"] = t["Wertstellungsdatum"].strftime("%a, %d. %b")
        t["Von/An"] = t["Sender"] if t["Betrag"] > 0 else t["Empfaenger"]
        t["Betrag"] /= 100
        t["CatStatus"] = CategoryStatus.NONE.value


def make_datatable(transactions, cats):
    transform_for_datatable(transactions)
    money = Format(
        scheme=Scheme.fixed,
        precision=2,
        group=Group.yes,
        groups=3,
        group_delimiter='.',
        decimal_delimiter=',',
        symbol=Symbol.yes,
        symbol_suffix=u'€'
    )

    return dash_table.DataTable(
        data=transactions,
        id="trans_table",
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
            {"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in transactions
        ],
        tooltip_duration=None,
        style_header={"backgroundColor": "rgb(210, 210, 210)", "fontSize": "110%"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{Betrag} > 0"},
                "color": "green"
            },
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(240, 240, 240)"
            },
        ],
        dropdown={
            "Kategorie": {
                "options": [
                    {"label": i[1], "value": i[0]} for i in cats
                ]
            }
        },
        style_as_list_view=True
    )


def main():
    transactions = db_connector.select("02", "2026", [
        "Hash", "Wertstellungsdatum", "Sender", "Empfaenger", "Verwendungszweck",
        "Betrag", "Kategorie"
    ])
    cats = db_connector.select_categories()
    global CAT_IDS
    CAT_IDS = {}
    for cat in cats:
        CAT_IDS[cat[1]] = cat[0]  # maps category names to IDs

    table = make_datatable(transactions, cats)

    app = Dash()
    app.layout = html.Div([
        dcc.Button("Categorize!", id="cat_button", n_clicks=0),
        table
    ])
    app.run(debug=True)


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')
    main()

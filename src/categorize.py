import db_connector

from dash import dash_table, html, dcc, callback, Input, Output, State
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


MONTHS = ["Nulluar", "Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]


def match_category(transaction):
    for category, map in MAPPINGS.items():
        for field, terms in map.items():
            for term in terms:
                if transaction[field].lower().find(term) != -1:
                    return category
    return ""


@callback(
    Output("trans_table", "data"),
    Output("trans_table", "tooltip_data"),
    Output("trans_table", "dropdown"),
    Input("month_dropdown", "value"),
)
def select(month_iso):
    y, m = month_iso.split('-')
    transactions = db_connector.select(m, y, [
        "Hash", "Wertstellungsdatum", "Sender", "Empfaenger", "Verwendungszweck",
        "Betrag", "Kategorie"
    ])
    transform_for_datatable(transactions)

    cats = db_connector.select_categories()
    global CAT_IDS
    CAT_IDS = {}
    for cat in cats:
        CAT_IDS[cat[1]] = cat[0]  # maps category names to IDs

    return (
        transactions,  # data
        [{"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in transactions],  # tooltip data
        {
            "Kategorie": {
                "options": [
                    {"label": i[1], "value": i[0]} for i in cats
                ]
            }
        }  # dropdown
    )


@callback(
    Output("trans_table", "data", allow_duplicate=True),
    Input("cat_button", "n_clicks"),
    State("trans_table", "data"),
    prevent_initial_call=True
)
def categorize(n_clicks, data):
    global CAT_IDS
    for t in data:
        if t["Kategorie"] is not None:
            continue
        t["Kategorie"] = CAT_IDS[match_category(t)]
    return data


@callback(
    Input("save_button", "n_clicks"),
    State("trans_table", "data"),
    prevent_initial_call=True
)
def save(n_clicks, data):
    db_connector.update_categories(data)


def transform_for_datatable(transactions):
    # transactions.sort(key=lambda t: t["Wertstellungsdatum"])
    for t in transactions:
        t["Datum"] = t["Wertstellungsdatum"].strftime("%a, %d. %b")
        t["Von/An"] = t["Sender"] if t["Betrag"] > 0 else t["Empfaenger"]
        t["Betrag"] /= 100


def make_datatable():
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
        data=[],
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
            {
                "if": {"column_id": "Betrag"},
                "textAlign": "right"
            },
            {
                "if": {"column_id": "Verwendungszweck"},
                "maxWidth": "400px",
                "overflow": "hidden",
                "textOverflow": "ellipsis"
            },
        ],
        # tooltip_data=[
        #     {"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in transactions
        # ],
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
            }
        ],
        # dropdown={
        #     "Kategorie": {
        #         "options": [
        #             {"label": i[1], "value": i[0]} for i in cats
        #         ]
        #     }
        # },
        style_as_list_view=True
    )


def create_categorizer() -> html.Div:
    table = make_datatable()
    months_iso = db_connector.select_months()
    months_human = [f"{MONTHS[int(month)]} {year}" for year, month in [date.split('-') for date in months_iso]]

    return html.Div([
        html.Div(
            [
                dcc.Dropdown(id="month_dropdown", options=[{"label": h, "value": m} for h, m in zip(months_human, months_iso)],
                             value=months_iso[-1], clearable=False),
                html.Div([
                    # dcc.Button("Reload", id="reload_button", n_clicks=0, style={"marginRight": "10px"}),
                    dcc.Button("Categorize!", id="cat_button", n_clicks=0, style={"marginRight": "10px"}),
                    dcc.Button("Save!", id="save_button", n_clicks=0)
                ]),
            ],
            style={
                "position": "sticky",
                "top": "5px",
                "backgroundColor": "white",
                "padding": "10px",
                "display": "flex",
                "justifyContent": "space-between",
                "zIndex": 99
            }
        ),
        table,
    ])

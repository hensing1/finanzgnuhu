import src.db_connector as db_connector

from dash import html, dcc, callback, Input, Output
import dash_ag_grid as dag


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


def make_grid():
    locale = """d3.formatLocale({
        "decimal": ",",
        "thousands": ".",
        "grouping": [3],
        "currency": ["", "€"],
        "nan": "",
    })"""

    cats = db_connector.select_categories()
    cat_id_to_name = {j[0]: j[1] for j in cats}
    print(cat_id_to_name)  # this works
    # cat_name_to_id = {i[1]: i[0] for i in cats}

    return dag.AgGrid(
        id="trans_grid",
        rowData=[],
        columnDefs=[
            # {"field": "Einnahme", "headerName": "ign"},
            {"field": "Datum", "headerName": "Datum"},
            {"field": "Von/An", "headerName": "Von/An"},
            {"field": "Verwendungszweck", "headerName": "Zweck"},
            {"field": "Betrag", "headerName": "Betrag",
             "valueFormatter":
                {"function": f"params.value ? {locale}.format('$,.2f')(params.value) : null"}},
            {
                "field": "Kategorie",
                "headerName": "Kategorie",
                "editable": True,
                'cellEditor': 'agRichSelectCellEditor',
                'cellEditorParams': {
                    'values': [cat[0] for cat in cats],
                    "formatValue": {
                        "function": "return params.context.value_map[params.value];"
                    },
                },
                "valueFormatter": {
                    "function": "return params.context.value_map[params.value];"
                }
                # all this shit does not work I cannot be bothered
            }
        ],
        dashGridOptions={"context": {"value_map": cat_id_to_name}}
    )


def transform_for_grid(transactions):
    # transactions.sort(key=lambda t: t["Wertstellungsdatum"])
    for t in transactions:
        t["Datum"] = t["Wertstellungsdatum"].strftime("%a, %d. %b")
        t["Von/An"] = t["Sender"] if t["Betrag"] > 0 else t["Empfaenger"]
        t["Betrag"] /= 100


@callback(
    Output("trans_grid", "rowData"),
    # Output("trans_table", "tooltip_data"),
    # Output("trans_table", "dropdown"),
    Input("month_dropdownn", "value"),
)
def select(month_iso):
    y, m = month_iso.split('-')
    transactions = db_connector.select_transactions(m, y, [
        "Hash", "Wertstellungsdatum", "Sender", "Empfaenger", "Verwendungszweck",
        "Betrag", "Kategorie", "Einnahme"
    ])
    transform_for_grid(transactions)

    # cats = db_connector.select_categories()
    # global CAT_IDS
    # CAT_IDS = {}
    # for cat in cats:
    #     CAT_IDS[cat[1]] = cat[0]  # maps category names to IDs

    # print(transactions)

    return (
        transactions  # data
        # [{"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in transactions],  # tooltip data
        # {
        #     "Kategorie": {
        #         "options": [
        #             {"label": i[1], "value": i[0]} for i in cats
        #         ]
        #     }
        # }  # dropdown
    )


def create_nategorizer() -> html.Div:
    table = make_grid()
    months_iso = db_connector.select_months()
    months_human = [f"{MONTHS[int(month)]} {year}" for year, month in [date.split('-') for date in months_iso]]

    return html.Div([
        html.Div(
            [
                dcc.Dropdown(id="month_dropdownn", options=[{"label": h, "value": m} for h, m in zip(months_human, months_iso)],
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

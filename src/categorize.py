import src.db_connector as db_connector

import dash_bootstrap_components as dbc
from dash import dash_table, html, dcc, callback, Input, Output, State
from dash.dash_table.Format import Format, Scheme, Group, Symbol

import json


CAT_FILE = "data/categories.json"


def parse_cat_file() -> dict:
    with open(CAT_FILE, 'r') as file:
        j = json.load(file)
    return j


def read_cat_file() -> [str]:
    with open(CAT_FILE, 'r') as file:
        return file.read()


@callback(
    Output("is_valid", "children"),
    Output("is_valid", "style"),
    Output("cat_save_button", "disabled"),
    Input("edit_area", "value")
)
def on_text_changed(text):
    is_valid_style = {"color": "green", "margin-bottom": 0}
    try:
        json.loads(text)
    except json.JSONDecodeError:
        is_valid_style["color"] = "fireBrick"
        return [["❌ ungültiges JSON"], is_valid_style, True]
    else:
        return [["✅ gültiges JSON"], is_valid_style, False]


@callback(
    State("edit_area", "value"),
    Input("cat_save_button", "n_clicks")
)
def save_categories(text, _):
    json.loads(text)
    with open(CAT_FILE, 'w') as file:
        file.write(text)


@callback(
    Output("cat_editor_modal", "is_open"),
    [Input("cat_edit_button", "n_clicks"), Input("cat_save_button", "n_clicks")],
    [State("cat_editor_modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


def make_editor():
    content = read_cat_file()
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Kategorien anpassen"), close_button=True),
            dbc.ModalBody([
                dcc.Textarea(
                    id="edit_area",
                    value=content,
                    style={
                        "height": 400,
                        "minHeight": 200,
                        "maxHeight": "70vh",
                        "fontFamily": "monospace, monospace",
                        "resize": "vertical"
                    }
                ),
                html.P(id="is_valid"),
            ]),
            dbc.ModalFooter(
                dcc.Button("Kategorien speichern", id="cat_save_button", style={"float": "right"})
            ),
        ],
        id="cat_editor_modal",
        size="xl",
        centered=True,
        is_open=False,
    )


def match_category(transaction, mappings):
    for category, map in mappings.items():
        for field, terms in map.items():
            for term in terms:
                if transaction[field].lower().find(term) != -1:
                    return category
    return ""


@callback(
    Output("trans_table", "data"),
    Output("trans_table", "tooltip_data"),
    Output("trans_table", "dropdown"),
    Input("sankey_range", "start_date"),
    Input("sankey_range", "end_date"),
)
def select(start_date, end_date):
    transactions = db_connector.select_transactions(start_date, end_date, [
        "Hash", "Wertstellungsdatum", "Sender", "Empfaenger", "Verwendungszweck",
        "Betrag", "Kategorie", "ignorieren"
    ])
    transform_for_datatable(transactions)

    cats = db_connector.select_categories()
    global CAT_IDS
    CAT_IDS = {cat[1]: cat[0] for cat in cats}  # maps category names to IDs

    return (
        transactions,  # data
        [{"Verwendungszweck": {"value": row["Verwendungszweck"]}} for row in transactions],  # tooltip data
        {
            "Kategorie": {
                "options": [
                    {"label": i[1], "value": i[0]} for i in cats
                ],
                "clearable": False
            }
        }  # dropdown
    )


@callback(
    Output("trans_table", "data", allow_duplicate=True),
    Output("trans_table", "selected_rows"),
    Input("ignore_button", "n_clicks"),
    State("trans_table", "data"),
    State("trans_table", "selected_rows"),
    prevent_initial_call=True
)
def toggle_ignore(_, data, rows):
    tuples = []
    for row in rows:
        new_state = data[row]["ignorieren"] != "True"
        data[row]["ignorieren"] = str(new_state)
        tuples.append((new_state, data[row]["Hash"]))
    db_connector.update_ignored(tuples)
    return data, []


@callback(
    Output("ignore_button", "disabled"),
    Input("trans_table", "selected_rows"),
    prevent_initial_call=True
)
def activate_ignore_button(selected_rows):
    return len(selected_rows) == 0


@callback(
    Output("trans_table", "data", allow_duplicate=True),
    State("trans_table", "data"),
    Input("cat_button", "n_clicks"),
    prevent_initial_call=True
)
def categorize(data, _):
    global CAT_IDS
    with open(CAT_FILE, 'r') as file:
        mappings = dict(json.load(file))
    for t in data:
        if t["Kategorie"] != 0:
            continue
        c = match_category(t, mappings)
        t["Kategorie"] = CAT_IDS[c]
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
        t["ignorieren"] = str(t["ignorieren"])


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
        tooltip_duration=None,
        style_header={"color": "rgb(49.8% 29.41% 76.86%)",
                      "backgroundColor": "rgb(245, 245, 245)", "fontSize": "120%"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{Betrag} > 0"},
                "color": "green"
            },
            # {
            #     "if": {"row_index": "odd"},
            #     "backgroundColor": "rgb(240, 240, 240)"
            # },
            {
                "if": {"filter_query": "{ignorieren} = True"},
                "backgroundColor": "lightGrey",
                "color": "rgb(110, 110, 110)"
            }
        ],
        style_as_list_view=True,
        row_selectable="multi",
        cell_selectable=False
    )


def create_categorizer() -> html.Div:
    table = make_datatable()
    # months_iso = db_connector.select_months()
    # months_human = [f"{MONTHS[int(month)]} {year}" for year, month in [date.split('-') for date in months_iso]]

    return html.Div(
        [
            make_editor(),
            html.Div(  # header with buttons
                [
                    # dcc.Dropdown(id="month_dropdown", options=[{"label": h, "value": m} for h, m in zip(months_human, months_iso)],
                    #              value=months_iso[-1], clearable=False),
                    dcc.Button("Ignorieren", id="ignore_button", n_clicks=0, disabled=True),
                    html.Div([
                        dcc.Button("Kategorie-Pattern bearbeiten", id="cat_edit_button", style={"marginRight": "10px"}),
                        dcc.Button("Kategorisieren", id="cat_button", n_clicks=0, style={"marginRight": "10px"}),
                        dcc.Button("Speichern", id="save_button", n_clicks=0)
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
            html.Div(
                [
                    table,
                    html.Div([], style={"height": "200px"}),  # this exists solely to make space for the dropdown in the bottom-most line
                ]
            )
        ],
        style={
            "maxHeight": "calc(100vh - 188px)",  # 100% minus the height of the tab bar and date controls
            "overflow": "scroll"
        }
    )

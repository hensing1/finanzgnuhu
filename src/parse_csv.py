import base64
import csv
import hashlib
from enum import Enum

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

import src.db_connector as db_connector


class Bank(Enum):
    ING = "ING"
    BBB = "BBBank / Bensberger"


def parse_ing(bin_str):
    lines = bin_str.decode("ISO-8859-1").split("\n")

    iban = lines[2].split(";")[1].replace(" ", "")

    reader = csv.DictReader(lines[13:], delimiter=";")

    return list(reader)[::-1], iban


def parse_bbb(bin_str):
    lines = bin_str.decode("utf-8").split("\n")

    lines[0] = (
        lines[0][1:]
        .replace("Buchungstag", "Buchung")
        .replace("Valutadatum", "Wertstellungsdatum")
        .replace("Name Zahlungsbeteiligter", "Auftraggeber/Empfänger")
        .replace("IBAN Auftragskonto", "IBAN")
        .replace("Waehrung", "Währung")
        .replace("Saldo nach Buchung", "Saldo")
    )

    transactions = list(csv.DictReader(lines, delimiter=";"))[::-1]
    return transactions, transactions[0]["IBAN"]


def to_ct(money_str):
    return int(float(money_str.replace(".", "").replace(",", ".")) * 100)


def to_iso_date(date):
    day, month, year = date.split(".")
    return f"{year}-{month}-{day}"


def sha256(transaction):
    id_fields = [
        "Wertstellungsdatum",
        "Auftraggeber/Empfänger",
        "Buchungstext",
        "Verwendungszweck",
        "Saldo",
        "Betrag",
        "IBAN",
    ]

    id_str = "".join([str(transaction[field]) for field in id_fields])
    h = hashlib.new("sha256")
    h.update(id_str.encode("utf-8"))
    return h.hexdigest()


def enrich(transactions, iban):
    """Modify 'transactions' in-place"""

    # Reihenfolge für Transaktionen eintragen
    last_date = ""
    n = 0
    for i in range(len(transactions)):
        if transactions[i]["Wertstellungsdatum"] != last_date:
            last_date = transactions[i]["Wertstellungsdatum"]
            n = 1
        transactions[i]["Tagesnummer"] = 10 * n
        n += 1

        # Korrekte Datentypen
        transactions[i]["Saldo"] = to_ct(transactions[i]["Saldo"])
        transactions[i]["Betrag"] = to_ct(transactions[i]["Betrag"])

        # in Einnahmen/Ausgaben aufteilen
        is_gain = transactions[i]["Betrag"] >= 0

        partner = transactions[i]["Auftraggeber/Empfänger"]
        assert partner is not None
        me = "ich"
        if is_gain:
            transactions[i]["Sender"] = partner
            transactions[i]["Empfaenger"] = me
        else:
            transactions[i]["Sender"] = me
            transactions[i]["Empfaenger"] = partner

        transactions[i]["Einnahme"] = is_gain

        # restliche Felder
        transactions[i]["Buchung"] = to_iso_date(transactions[i]["Buchung"])
        transactions[i]["Wertstellungsdatum"] = to_iso_date(
            transactions[i]["Wertstellungsdatum"]
        )
        transactions[i]["IBAN"] = iban
        transactions[i]["Hash"] = sha256(transactions[i])
        transactions[i]["Kategorie"] = 0
        transactions[i]["ignorieren"] = False


def parse_csv(bank: str, csv_content):
    file_parser = {Bank.BBB.value: parse_bbb, Bank.ING.value: parse_ing}[bank]
    content_type, content_string = csv_content.split(",")
    decoded = base64.b64decode(content_string)

    transactions, iban = file_parser(decoded)
    enrich(transactions, iban)

    return transactions, iban


@callback(
    Output("new_csv_modal", "is_open"),
    [Input("new_csv_button", "n_clicks")],
    [State("new_csv_modal", "is_open")],
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


@callback(
    Output("csv_buffer", "data"),
    Input("bank_selector", "value"),
    Input("csv_upload", "contents"),
    prevent_initial_call=True
)
def parse_csv_callback(bank, content):
    if content is None:
        raise PreventUpdate

    try:
        transactions, iban = parse_csv(bank, content)
    except UnicodeDecodeError, KeyError:
        return dict()

    existing_accs = db_connector.select_accounts()
    ibans = {acc["IBAN"] for acc in existing_accs}
    acc_exists: bool = iban in ibans
    acc_name = next((acc["Name"] for acc in existing_accs if acc["IBAN"] == iban), "")

    return {
        "transactions": transactions,
        "iban": iban,
        "num_new_transactions": db_connector.num_of_new_transactions(transactions),
        "account_exists": acc_exists,
        "account_name": acc_name
    }


@callback(
    Output("csv_upload_button", "disabled"),
    Input("csv_buffer", "data"),
    Input("new_account_name", "value"),
    prevent_initial_call=True
)
def set_csv_upload_button_disabled(csv_data, acc_name):
    return \
        csv_data is None or \
        len(csv_data) == 0 or \
        len(csv_data["transactions"]) == 0 or \
        csv_data["num_new_transactions"] == 0 or \
        (not csv_data["account_exists"] and (acc_name is None or acc_name == ""))


@callback(
    Output("parsed_csv_summary", "children"),
    Input("csv_buffer", "data"),
    State("bank_selector", "value"),
    State("csv_upload", "filename"),
    prevent_initial_call=True
)
def set_csv_summary(csv_data, bank, filename):
    summary = [html.P(["Datei: ", html.Code(filename)])]

    if len(csv_data) == 0:
        summary += [html.P(f"Datei kann mit Parser für {bank} nicht dekodiert werden.")]
        return summary

    acc_desc = csv_data["account_name"] if csv_data["account_exists"] else csv_data["iban"]
    info = [
        f"Die Datei enhält {len(csv_data['transactions'])} Transaktionen "
        "für Konto ", html.I(acc_desc), "."
    ]
    if len(csv_data["transactions"]) > 0:
        info += [f" Davon sind {csv_data['num_new_transactions']} noch nicht"
                 " in der Datenbank."]

    summary += [html.P(info)]
    return summary


@callback(
    Output("new_account_div", "style"),
    Input("csv_buffer", "data"),
    State("new_account_div", "style"),
    prevent_initial_call=True
)
def set_new_account_dialog_visible(csv_data, new_acc_css):
    visible = \
        len(csv_data) > 0 and \
        csv_data["num_new_transactions"] > 0 and \
        not csv_data["account_exists"]
    new_acc_css["display"] = "inherit" if visible else "none"
    return new_acc_css


@callback(
    Output("insert_ok_text", "children"),
    Output("insert_ok_modal", "is_open"),
    Output("new_csv_modal", "is_open", allow_duplicate=True),
    State("bank_selector", "value"),
    State("csv_upload", "contents"),
    State("new_account_name", "value"),
    Input("csv_upload_button", "n_clicks"),
    prevent_initial_call=True,
)
def on_csv_upload(bank, content, new_acc_name, _):
    ok_text = []
    transactions, iban = parse_csv(bank, content)

    existing_accs = db_connector.select_accounts()
    ibans = {acc["IBAN"] for acc in existing_accs}
    if iban not in ibans:
        db_connector.insert_account(iban, new_acc_name, bank)
        ok_text += ["Neues Konto angelegt: ", html.I(new_acc_name), ".", html.Br()]
        acc_name = new_acc_name
    else:
        acc_name = next(acc["Name"] for acc in existing_accs if acc["IBAN"] == iban)

    num_inserted = db_connector.insert(transactions)
    ok_text += [
        f"{num_inserted} Transaktionen für Konto ",
        html.I(acc_name),
        " eingefügt.",
    ]
    return [ok_text, True, False]


def create_csv_uploader(label="Neuer Kontoauszug"):
    return html.Div(
        [
            dcc.Button(
                label,
                id="new_csv_button",
                style={
                    "background": "var(--Dash-Fill-Interactive-Strong)",
                    "color": "white",
                },
            ),
            dcc.Store(id="csv_buffer"),
            dbc.Modal(
                [
                    dbc.ModalHeader(),
                    dbc.ModalFooter(
                        html.P(id="insert_ok_text"),
                        style={"justify-content": "flex-start"},
                    ),
                ],
                id="insert_ok_modal",
                is_open=False,
                size="sm",
                centered=True,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Kontoauszug hochladen")),
                    dbc.ModalBody(
                        [
                            html.P(
                                "Bank auswählen:", style={"display": "inline-block"}
                            ),
                            dcc.Dropdown(
                                sorted([b.value for b in Bank]),
                                Bank.ING.value,
                                id="bank_selector",
                                clearable=False,
                                style={
                                    "display": "inline-block",
                                    "width": "200px",
                                    "margin-left": "10px",
                                },
                            ),
                            dcc.Upload(
                                "CSV-Datei auswählen oder hierher ziehen",
                                id="csv_upload",
                                accept="text/csv",
                                style={
                                    "width": "100%",
                                    "height": "60px",
                                    "lineHeight": "60px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "cursor": "copy",
                                },
                            ),
                            html.Div(id="parsed_csv_summary"),
                            html.Div(
                                id="new_account_div",
                                children=[
                                    html.P("Dem neuen Konto einen Namen geben:"),
                                    dcc.Input(id="new_account_name"),
                                ],
                                style={"display": "none"},
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        dcc.Button("Hochladen", id="csv_upload_button", disabled=True)
                    ),
                ],
                id="new_csv_modal",
                is_open=False,
                centered=True,
            ),
        ]
    )

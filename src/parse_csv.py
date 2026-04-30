import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State

import base64
import csv
import hashlib

import src.db_connector as db_connector


def parse_ing(bin_str):
    # with open(filename, "rb") as file:
    #     lines = file.read().decode("ISO-8859-1").split("\n")
    lines = bin_str.decode("ISO-8859-1").split("\n")

    iban = lines[2].split(";")[1].replace(" ", "")

    reader = csv.DictReader(lines[13:], delimiter=";")

    return list(reader)[::-1], iban


def parse_bbb(bin_str):
    # with open(filename, "r") as file:
    #     lines = file.readlines()
    lines = bin_str.decode("utf-8").split("\n")

    lines[0] = lines[0][1:] \
        .replace("Buchungstag", "Buchung") \
        .replace("Valutadatum", "Wertstellungsdatum") \
        .replace("Name Zahlungsbeteiligter", "Auftraggeber/Empfänger") \
        .replace("IBAN Auftragskonto", "IBAN") \
        .replace("Waehrung", "Währung") \
        .replace("Saldo nach Buchung", "Saldo")

    transactions = list(csv.DictReader(lines, delimiter=";"))[::-1]
    return transactions, transactions[0]["IBAN"]


def to_ct(money_str):
    return int(float(money_str.replace(".", "").replace(",", ".")) * 100)


def to_iso_date(date):
    day, month, year = date.split(".")
    return f"{year}-{month}-{day}"


def sha256(transaction):
    id_fields = ['Wertstellungsdatum', 'Auftraggeber/Empfänger',
                 'Buchungstext', 'Verwendungszweck', 'Saldo', 'Betrag', 'IBAN']

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
        assert (partner is not None)
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
            transactions[i]["Wertstellungsdatum"])
        transactions[i]["IBAN"] = iban
        transactions[i]["Hash"] = sha256(transactions[i])
        transactions[i]["Kategorie"] = 0
        transactions[i]["ignorieren"] = False


@callback(
    Output("new_csv_modal", "is_open"),
    [Input("new_csv_button", "n_clicks")],
    [State("new_csv_modal", "is_open")],
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


def parse_csv(bank, csv_content):
    file_parser = {
        "BBBank": parse_bbb,
        "ING": parse_ing
    }[bank]
    content_type, content_string = csv_content.split(',')
    decoded = base64.b64decode(content_string)

    transactions, iban = file_parser(decoded)
    enrich(transactions, iban)

    return transactions, iban


@callback(
    Output("parsed_csv_summary", "children"),
    Output("new_account_div", "style"),
    Output("csv_upload_button", "disabled"),
    Input("bank_selector", "value"),
    Input("csv_upload", "contents"),
    State("csv_upload", "filename"),
    State("new_account_div", "style"),
    prevent_initial_call=True
)
def on_csv_dropped(bank, content, filename, new_acc):
    try:
        transactions, iban = parse_csv(bank, content)
    except UnicodeDecodeError:
        return [
            [  # csv summary
                html.P(["Datei: ", html.Code(filename)]),
                html.P(f"Datei kann mit Parser für {bank} nicht dekodiert werden.")
            ],
            new_acc,
            True
        ]

    new_ts = db_connector.num_of_new_transactions(transactions)

    existing_accs = db_connector.select_accounts()
    ibans = {acc["IBAN"] for acc in existing_accs}
    if iban not in ibans:
        new_acc["display"] = "inherit"  # make dialog for new acc-name visible

    return [
        [  # csv summary
            html.P(["Datei: ", html.Code(filename)]),
            html.P(f"Datei enhält {len(transactions)} Transaktionen für Konto {iban}, "
                   f"{new_ts} davon sind noch nicht in der Datenbank.")
        ],
        new_acc,
        new_ts == 0  # csv_upload_button.disabled
    ]


@callback(
    Output("insert_ok_text", "children"),
    Output("insert_ok_modal", "is_open"),
    Output("new_csv_modal", "is_open", allow_duplicate=True),
    State("bank_selector", "value"),
    State("csv_upload", "contents"),
    Input("csv_upload_button", "n_clicks"),
    prevent_initial_call=True
)
def on_csv_upload(bank, content, _):
    transactions, iban = parse_csv(bank, content)
    num_inserted = db_connector.insert(transactions)
    return [[f"{num_inserted} Transaktionen für Konto {iban} eingefügt."], True, False]


def create_csv_uploader():
    return html.Div(
        [
            dcc.Button("Neuer Kontoauszug", id="new_csv_button", style={"background": "var(--Dash-Fill-Interactive-Strong)", "color": "white"}),
            dbc.Modal(
                [
                    dbc.ModalHeader(),
                    dbc.ModalFooter(
                        html.P(id="insert_ok_text"),
                        style={"justify-content": "flex-start"}
                    )
                ],
                id="insert_ok_modal",
                is_open=False,
                size="sm",
                centered=True
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Kontoauszug hochladen")),
                    dbc.ModalBody([
                        html.P("Bank auswählen:", style={"display": "inline-block"}),
                        dcc.Dropdown(
                            ["BBBank", "ING"],
                            "ING",
                            id="bank_selector",
                            clearable=False,
                            style={"display": "inline-block", "width": "200px", "margin-left": "10px"}
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
                                "cursor": "copy"
                            },
                        ),
                        html.Div(id="parsed_csv_summary"),
                        html.Div(
                            id="new_account_div",
                            children=[
                                html.P("Name für neues Konto eingeben:"),
                                dcc.Input(id="new_account_name")
                            ],
                            style={
                                "display": "none"
                            }
                        )
                    ]),
                    dbc.ModalFooter(
                        dcc.Button("Hochladen", id="csv_upload_button", disabled=True)
                    ),
                ],
                id="new_csv_modal",
                is_open=False,
                centered=True
            )
        ]
    )


# def main(filename, bank):
#     file_parser = {
#         "bbbank": parse_bbb,
#         "ing": parse_ing
#     }[bank]
#     transactions, iban = file_parser(filename)
#
#     enrich(transactions, iban)
#
#     # for line in transactions:
#     #     print(line)
#     insert(transactions)
#
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description=".csv-Export von der Bank in die Datenbank packen")
#     parser.add_argument("Dateiname")
#     parser.add_argument(
#         "-b", "--bank", choices=["bbbank", "ing"], default="ing")
#     args = parser.parse_args()
#     main(args.Dateiname, args.bank)

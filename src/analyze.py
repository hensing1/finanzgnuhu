from sys import argv
import locale

from dash import Dash, html, dcc
from plotly import graph_objects as go


FILTER = [
    [("Sender", "martin lehmann"), ("Verwendungszweck", "studium plus")],
    [("Sender", "henning lehmann")],
    [("Empfaenger", "henning lehmann")],
]

MONTHS = ["Nulluar", "Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]

# class SankeyNode:
#     def __init__(self, label: str, id: int):
#         self.label = label
#         self.id = id




def match_filter(filter, transaction):
    for k, v in filter:
        if transaction[k].lower().find(v) == -1:
            return False
    return True


def match_any_filter(transaction):
    for f in FILTER:
        if match_filter(f, transaction):
            print(f"Filtered: {transaction['Sender']} --{transaction['Betrag'] / 100}-> {
                  transaction['Empfaenger']} ({transaction['Verwendungszweck']})")
            return True
    return False






def ein_aus(transactions):
    sum_ein = sum([t['Betrag'] for t in transactions if t['Einnahme']])
    sum_aus = sum([abs(t['Betrag']) for t in transactions if not t['Einnahme']])
    return sum_ein, sum_aus


def main(argv):
    locale.setlocale(locale.LC_ALL, '')
    ts = select_all()
    ts = [t for t in ts if not match_any_filter(t)]

    content = [html.H1("Die Nanzen")]

    for y, m in [(2026, 2), (2026, 1), (2025, 12), (2025, 11), (2025, 10), (2025, 9),
                 (2025, 8), (2025, 7), (2025, 6), (2025, 5), (2025, 4),
                 (2025, 3), (2025, 2)]:
        content.append(html.H2(f"{MONTHS[m]} {y}"))
        transactions = [t for t in ts
                        if t['Wertstellungsdatum'].year == y and t['Wertstellungsdatum'].month == m]
        sankey = make_sankey(transactions)
        content.append(dcc.Graph(figure=go.Figure(sankey)))

        ein, aus = ein_aus(transactions)
        content.append(html.P(f"Einnahmen: {locale.format_string('%.2f', ein / 100, grouping=True)}€, "
                              f"Ausgaben: {locale.format_string('%.2f', aus / 100, grouping=True)}€"))

    app = Dash("Die Nanzen")

    app.layout = html.Div(content)

    app.run(debug=True)


if __name__ == "__main__":
    main(argv)

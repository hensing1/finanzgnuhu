from sys import argv
import csv

import sqlite3 as sql
import hashlib


def read_umsatzanzeige_as_list(filename):
    with open(argv[1], "rb") as file:
        lines = file.read().decode("ISO-8859-1").split("\n")

    iban = lines[2].split(";")[1].replace(" ", "")

    reader = csv.DictReader(lines[13:], delimiter=";")

    return list(reader)[::-1], iban


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


def insert(transactions):
    con = sql.connect("transaktionen.db")
    cur = con.cursor()
    res = cur.execute("""
        select Hash from Umsaetze where Hash in (%s);
    """ % ", ".join([f"'{t["Hash"]}'" for t in transactions]))

    excluded = {r[0] for r in res.fetchall()}

    filtered_transactions = tuple(
        t for t in transactions if t["Hash"] not in excluded)

    cur.executemany("""
        insert into Umsaetze values(
            :Hash, :IBAN, :Buchung, :Wertstellungsdatum, :Tagesnummer, :Sender,
            :Empfaenger, :Buchungstext, :Verwendungszweck, :Saldo, :Betrag,
            :Einnahme
        );
    """, filtered_transactions)

    con.commit()
    con.close()


def main(argv):
    transactions, iban = read_umsatzanzeige_as_list(argv[1])
    enrich(transactions, iban)
    # print(transactions[:2])
    insert(transactions)


if __name__ == "__main__":
    main(argv)

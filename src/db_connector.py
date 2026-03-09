from datetime import datetime
import sqlite3 as sql

SQLITE_FILE = "../transaktionen.db"


def str_to_date(datestr):
    year, month, day = datestr.split("-")
    return datetime(int(year), int(month), int(day))


def set_dates(transactions):
    if len(transactions) == 0:
        return

    if "Wertstellungsdatum" in transactions[0].keys():
        for t in transactions:
            t['Wertstellungsdatum'] = str_to_date(t['Wertstellungsdatum'])
    if "Buchung" in transactions[0].keys():
        for t in transactions:
            t['Buchung'] = str_to_date(t['Buchung'])


def convert_sql_types_to_python(transactions):
    set_dates(transactions)


def insert(transactions):
    con = sql.connect(SQLITE_FILE)
    cur = con.cursor()
    res = cur.execute("""
        select Hash from Umsaetze where Hash in (%s);
    """ % ", ".join([f"'{t["Hash"]}'" for t in transactions]))

    excluded = {r[0] for r in res.fetchall()}

    filtered_transactions = tuple(
        t for t in transactions if t["Hash"] not in excluded)

    ans = ""
    while ans != "y" and ans != "yes":
        ans = input(f"Continue to insert {len(filtered_transactions)}"
                    f" of {len(transactions)} transactions? (y/n): ").lower()
        if ans == "n" or ans == "no":
            con.close()
            return

    cur.executemany("""
        insert into Umsaetze values(
            :Hash, :IBAN, :Buchung, :Wertstellungsdatum, :Tagesnummer, :Sender,
            :Empfaenger, :Buchungstext, :Verwendungszweck, :Saldo, :Betrag,
            :Einnahme, :Kategorie
        );
    """, filtered_transactions)

    con.commit()
    con.close()


def select(month, year, columns=None):
    if not columns:
        columns = ["*"]

    with sql.connect(SQLITE_FILE) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        res = cur.execute(f"""
            select {', '.join(columns)} from Umsaetze where
                strftime('%Y', Wertstellungsdatum) = ? and
                strftime('%m', Wertstellungsdatum) = ?;""", (year, month))
        lines = res.fetchall()

    transactions = [dict(t) for t in lines]
    convert_sql_types_to_python(transactions)
    return transactions


def select_all():
    con = sql.connect(SQLITE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    res = cur.execute("select * from Umsaetze;")
    lines = res.fetchall()
    con.close()

    transactions = [dict(t) for t in lines]
    convert_sql_types_to_python(transactions)
    return transactions


def select_categories():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute("select * from Kategorien;")
        lines = res.fetchall()
    return lines

from datetime import date
import sqlite3 as sql

SQLITE_FILE = "data/transaktionen.db"


def str_to_date(datestr):
    year, month, day = datestr.split("-")
    return date(int(year), int(month), int(day))


def set_dates(transactions):
    if len(transactions) == 0:
        return

    if "Wertstellungsdatum" in transactions[0].keys():
        for t in transactions:
            t['Wertstellungsdatum'] = str_to_date(t['Wertstellungsdatum'])
    if "Buchung" in transactions[0].keys():
        for t in transactions:
            t['Buchung'] = str_to_date(t['Buchung'])


def set_bools(transactions):
    if (len(transactions)) == 0:
        return

    if "Einnahme" in transactions[0].keys():
        for t in transactions:
            t["Einnahme"] = t["Einnahme"] == 1
    if "ignorieren" in transactions[0].keys():
        for t in transactions:
            t["ignorieren"] = t["ignorieren"] == 1


def convert_sql_types_to_python(transactions):
    set_dates(transactions)
    set_bools(transactions)


def num_of_new_transactions(transactions):
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute("""
            select Hash from Umsaetze where Hash in (%s);
        """ % ", ".join([f"'{t["Hash"]}'" for t in transactions]))
        return len(transactions) - len(res.fetchall())


def insert(transactions):
    with sql.connect(SQLITE_FILE) as con:
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
                :Einnahme, :Kategorie, :ignorieren
            );
        """, filtered_transactions)

        con.commit()

    return len(filtered_transactions)


def insert_account(iban, acc_name, bank):
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        cur.execute(
            """insert into Konten values(?, ?, ?, 'Girokonto');""",
            (iban, acc_name, bank)
        )
        con.commit()


def select_transactions_as_view(start_date, end_date):
    with sql.connect(SQLITE_FILE) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        res = cur.execute("""
            select  Wertstellungsdatum, Sender, Empfaenger, Verwendungszweck, Betrag,
                    Einnahme, ignorieren, Kategorien.Name as "KategorieName"
                from Umsaetze
                left join Kategorien on Umsaetze.Kategorie = Kategorien.ID
                where
                    ? <= Wertstellungsdatum and
                    Wertstellungsdatum <= ?
                order by Wertstellungsdatum desc, Tagesnummer desc;
        """, (start_date, end_date))
        lines = res.fetchall()

    transactions = [dict(t) for t in lines]
    convert_sql_types_to_python(transactions)
    return transactions


def select_transactions(start_date, end_date, columns=None):
    if not columns:
        columns = ["*"]

    with sql.connect(SQLITE_FILE) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        res = cur.execute(f"""
            select {', '.join(columns)} from Umsaetze
                where
                    ? <= Wertstellungsdatum and
                    Wertstellungsdatum <= ?
                order by Wertstellungsdatum asc, Tagesnummer asc;""", (start_date, end_date))
        lines = res.fetchall()

    transactions = [dict(t) for t in lines]
    convert_sql_types_to_python(transactions)
    return transactions


def select_latest_date():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute(
            "select Wertstellungsdatum "
            "from Umsaetze order by Wertstellungsdatum desc limit 1;")
        date = res.fetchone()
    return str_to_date(date[0])


def select_earliest_date():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute(
            "select Wertstellungsdatum "
            "from Umsaetze order by Wertstellungsdatum asc limit 1;")
        date = res.fetchone()
    return str_to_date(date[0])


def select_all():
    with sql.connect(SQLITE_FILE) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        res = cur.execute("select * from Umsaetze;")
        lines = res.fetchall()

    transactions = [dict(t) for t in lines]
    convert_sql_types_to_python(transactions)
    return transactions


def select_accounts():
    with sql.connect(SQLITE_FILE) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        res = cur.execute("select * from Konten;")
        lines = res.fetchall()
    return [dict(acc) for acc in lines]


def select_categories():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute("select * from Kategorien order by ID;")
        lines = res.fetchall()
    return lines


def select_months():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute("""
            select distinct strftime('%Y-%m', Wertstellungsdatum) as Datum
                from Umsaetze
                order by Datum asc;
        """)
        lines = res.fetchall()
    # return [(int(year), int(month)) for year, month in [line[0].split('-') for line in lines]]
    return [line[0] for line in lines]


def update_categories(entries):
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        cur.executemany("""
            update Umsaetze
                set Kategorie = :Kategorie
                where Hash = :Hash;
        """, entries)
        con.commit()


def update_ignored(tuples):
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        cur.executemany("""
            update Umsaetze
                set ignorieren = ?
                where Hash = ?;
        """, tuples)
        con.commit()


def select_aggregated_expenses():
    with sql.connect(SQLITE_FILE) as con:
        cur = con.cursor()
        res = cur.execute("""
            select
                sum(Betrag),
                strftime('%Y-%m', Wertstellungsdatum) as 'Monat',
                Kategorien.Name
            from Umsaetze
            left join Kategorien on Umsaetze.Kategorie = Kategorien.ID
            where not ignorieren and not Einnahme
            group by Monat, Kategorie;
        """)
        lines = res.fetchall()
    return lines

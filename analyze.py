from sys import argv
import sqlite3 as sql

MAPPINGS = {
    "Essen": {
        "Empfaenger": ["edeka", "rewe", "frittenwerk", "gastro",
                       "merzenich", "mcdonalds", "mensa", "backwerk", "subway"]
    },
    "Sparkonto": {"Empfaenger": ["kleingeld"]},
    "Bargeld": {"Empfaenger": ["bargeld"]},
    "Telefon": {"Empfaenger": ["congstar"]},
    "Auto": {
        "Empfaenger": ["aral"],
        "Verwendungszweck": ["kfz-steuer"]
    }
}

def select(month):
    con = sql.connect("transaktionen.db")
    cur = con.cursor()
    res = cur.execute("""
        select * from Umsaetze where
            strftime('%m', Wertstellungsdatum) = ?;""", month)
    



def main(argv):
    ...


if __name__ == "__main__":
    main(argv)

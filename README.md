# Finanzgnuhu

<img src="assets/gnuhu.png" width="512">

> Ein Analysetool für die persönlichen Finanzen zum selber hosten.

## Features

- Kategorisieren von einzelnen Transaktionen
- Visualisierung von beliebigen Zeiträumen mit Sankey-Diagramm
- Zusammenrechnung von Einnahmen und Ausgaben
- Beliebig viele Konten
- Auto-Kategorisierung mit pattern matching
- Möglichkeit, einzelne Transaktionen für die Auswertung zu ignorieren
- Alle Daten lokal in einer [SQLite-Datenbank](https://sqlite.org/about.html) (`data/transaktionen.db`)

## Nicht-Features

- Um Extra-Kategorien zu erstellen, muss man noch mit dem SQLite-Client seiner Wahl in die Datenbank klettern.
  - Default-Kategorien sind: `Reise`, `Essen`, `Sparkonto`, `Bargeld`, `Telefon`, `Auto`, `Gesundheit`, `Abos`, `Anschaffungen`, `Uni`, `Freizeit` und `Geschenke`.
- Nur Sankey-Diagramm. Dinge wie ein Balkendiagramm (um monatsweise die Ausgaben in einzelnen Kategorien zu tracken) sind noch im Ofen.
- Nur auf Deutsch.

**PRs welcome!**

## Anforderungen

- `python 3.14`
- [uv](https://docs.astral.sh/uv/) (empfohlen)

## Installation

Repo klonen: `git clone git@github.com:hensing1/finanzgnuhu --depth 1`

### Abhängigkeiten installieren

Mit uv:

```bash
uv sync
```

Mit pip:

```bash
python -m venv .venv
. .venv/bin/activate  # bzw. '. .venv/bin/activate.fish' für fish, etc.
pip install 'dash<5.0' pandas plotly[express] dash_bootstrap_components
```

### Ausführen

```bash
. .venv/bin/activate  # bzw. '. .venv/bin/activate.fish' für fish, etc.
python3 main.py       # beenden mit Strg+C
```

## Auto-Kategorisierung

Das Pattern-Matching wird in `data/categories.json` definiert. Die Datei kann auch innerhalb der App editiert werden.

Sie folgt dem folgenden Muster:

```json
{
  "<Kategorie>": {
    "<Feld 1>": ["<Pattern 1>", "<Pattern 2>", ...],
    "<Feld 2>": ["<Pattern 3>", ...]
  }
}
```

Bedeutet: damit eine Transaktion `<Kategorie>` zugeordnet wird, muss `<Feld 1>` das Pattern `<Pattern 1>` oder `<Pattern 2>`, oder `<Feld 2>` das Pattern `<Pattern 3>` enthalten. Die Groß-/Kleinschreibung von `<Pattern>` ist dabei egal.

Für eine Liste der Default-Kategorien, siehe [oben](#Nicht-Features).

Gültige Felder sind (Groß-/Kleinschreibung wichtig): `Sender`, `Empfaenger`, `Verwendungszweck` und `Wertstellungsdatum`.

Eine Beispiel-Kategorisierungsdatei wird bei der erstmaligen Ausführung angelegt.

## How does work

Die Anwendung läuft im Browser. Der Server ist [Dash](https://dash.plotly.com/). Die Graphen werden dynamisch erstellt mit [Plotly](https://plotly.com/python/sankey-diagram/).

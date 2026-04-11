import plotly.express as px
import pandas as pd

import db_connector as db_connector


# fig = px.bar(pd.DataFrame(data={
#     "monat":     ["januar", "januar", "februar", "februar"],
#     "kategorie": ["essen",  "miete",  "essen",   "miete"],
#     "wert":      [10,       20,       30,        50]
# }), x="monat", y="wert", color="kategorie", title="Die Dings")

expenses = db_connector.select_aggregated_expenses()
df = pd.DataFrame(data=expenses, columns=["Betrag", "Monat", "Kategorie"])
df["Betrag"] = abs(df["Betrag"]) / 100

fig = px.bar(df, x="Monat", y="Betrag", color="Kategorie", title="Die Dings")
fig.show()

import plotly.graph_objects as go

node_labels = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben"]
eingaben = [100, 20]
ausgaben = [20, 40, 10, 30, 20]

konto_id = len(eingaben) + len(ausgaben)
# connections = [(ein, konto_label) for ein, _ in enumerate(eingaben)]
# connections += [(konto_label, aus) for aus, _ in enumerate(ausgaben)]
s = []
t = []
for in_id, val in enumerate(eingaben):
    s.append(in_id)
    t.append(konto_id)

v = eingaben + ausgaben

for out_label, val in enumerate(ausgaben):
    s.append(konto_id)
    t.append(len(eingaben) + out_label + 9)

print(s)
print(t)

fig = go.Figure(
    data=[go.Sankey(
        node={"label": node_labels},
        link=dict(source=s, target=t, value=v)
    )]
)

fig.update_layout(title_text="hallo ein sankey")
fig.show()

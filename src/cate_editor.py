from dash import dcc, html, callback, Input, Output

import json

CATE_FILE = "data/categories.json"


def parse_cate_file() -> dict:
    with open(CATE_FILE, 'r') as file:
        j = json.load(file)
    return j


def read_cate_file() -> [str]:
    with open(CATE_FILE, 'r') as file:
        return file.read()


@callback(
    Output("is_valid", "children"),
    Output("is_valid", "style"),
    Input("edit_area", "value")
)
def on_text_changed(value):
    try:
        json.loads(value)
    except json.JSONDecodeError:
        return [["❌ JSON is not valid"], {"color": "red"}]
    else:
        return [["✅ JSON is valid"], {"color": "green"}]


def make_editor():
    content = read_cate_file()
    return html.Div(
        [
            html.Div(
                [
                    dcc.Textarea(
                        id="edit_area",
                        value=content,
                        style={
                            "height": 300,
                            "fontFamily": "monospace, monospace"
                        }
                    ),
                    html.P(id="is_valid")
                ],
                style={
                    "width": "75%",
                }
            ),
        ],
        style={"display": "flex", "justifyContent": "center"}
    )

# ===== Imports =====
from jupyter_dash import JupyterDash
import dash_leaflet as dl
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import base64, os, pandas as pd, re

from animal_shelter import AnimalShelter


db = AnimalShelter(db_name='aac', collection_name='outcomes')

# ===== Helpers =====
def to_df(records):
    df = pd.DataFrame.from_records(records)
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)
    return df


df_all = to_df(db.read({}))
fallback_cols = ["age_upon_outcome","animal_id","animal_type","breed","color",
                 "date_of_birth","datetime","monthyear","name","outcome_subtype",
                 "outcome_type","sex_upon_outcome","location_lat","location_long",
                 "age_upon_outcome_in_weeks"]
columns = [{"name": c, "id": c, "deletable": False, "selectable": True}
           for c in (df_all.columns if not df_all.empty else fallback_cols)]


logo_candidates = ["Grazioso Logo.jpg"]
logo_path = next((p for p in logo_candidates if os.path.exists(p)), None)
encoded_image = None
mime = None
if logo_path:
    with open(logo_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode()
    mime = "image/jpeg" if logo_path.lower().endswith((".jpg",".jpeg")) else "image/png"

brand_bar = html.Div([
    html.A(
        html.Img(src=(f"data:{mime};base64,{encoded_image}" if encoded_image else ""),
                 style={"height": "80px"}),
        href="https://www.snhu.edu", target="_blank", title="Grazioso Salvare"
    ),
    html.Div("Dashboard by Chris Phillips — CS-340",
             style={"fontWeight": "bold", "fontSize": "18px"})
], style={"display": "flex", "gap": "16px", "alignItems": "center"})

# ===== Filters =====
filters = html.Div([
    html.Div("Filter by Rescue Type:", style={"fontWeight": "bold"}),
    dcc.RadioItems(
        id="filter-type",
        options=[
            {"label": "Water Rescue", "value": "water"},
            {"label": "Mountain/Wilderness Rescue", "value": "mountain"},
            {"label": "Disaster / Individual Tracking", "value": "disaster"},
            {"label": "Reset (All)", "value": "reset"},
        ],
        value="reset",
        labelStyle={"display": "inline-block", "marginRight": "16px"}
    )
])

# ===== DataTable =====
datatable = dash_table.DataTable(
    id='datatable-id',
    columns=columns,
    data=df_all.to_dict('records'),
    page_size=10,
    sort_action="native",
    filter_action="native",
    row_selectable="single",
    selected_rows=[0],
    style_table={"overflowX":"auto"},
    style_cell={"textAlign":"left","minWidth":"100px","width":"120px","maxWidth":"280px"},
    style_header={"fontWeight":"bold"}
)

# ===== App Layout =====
app = JupyterDash(__name__)
app.layout = html.Div([
    brand_bar,
    html.Hr(),
    filters,
    html.Hr(),
    datatable,
    html.Br(), html.Hr(),
    html.Div(className='row', style={'display':'flex','gap':'12px'}, children=[
        html.Div(id='graph-id', className='col s12 m6', style={"flex":1}),
        html.Div(id='map-id', className='col s12 m6', style={"flex":1})
    ])
])

# ===== Query Builder (uses compiled regex in $in to avoid the $in/$regex error) =====
def breed_patterns(names):
    # compiled regex objects are allowed inside $in
    return [re.compile(n, re.IGNORECASE) for n in names]

BREEDS_WATER = breed_patterns([
    "Labrador Retriever", "Chesapeake Bay Retriever", "Newfoundland"
])

BREEDS_MOUNTAIN = breed_patterns([
    "German Shepherd", "Alaskan Malamute", "Old English Sheepdog", "Siberian Husky", "Rottweiler"
])

BREEDS_DISASTER = breed_patterns([
    "Doberman Pinscher", "German Shepherd", "Golden Retriever", "Bloodhound", "Rottweiler"
])

# Case-insensitive matches for animal_type and sex strings (robust to minor variants)
DOG_REGEX        = re.compile(r"^\s*dog\s*$", re.IGNORECASE)
INTACT_FEMALE_RX = re.compile(r"^\s*intact\s+female\s*$", re.IGNORECASE)
INTACT_MALE_RX   = re.compile(r"^\s*intact\s+male\s*$", re.IGNORECASE)

def build_query(ft: str) -> dict:
    base = [{"animal_type": DOG_REGEX}]  # always filter to dogs (case-insensitive)

    if ft == "water":
        base += [
            {"sex_upon_outcome": INTACT_FEMALE_RX},
            {"age_upon_outcome_in_weeks": {"$gte": 26, "$lte": 156}},
            {"breed": {"$in": BREEDS_WATER}},
        ]

    elif ft == "mountain":
        base += [
            {"sex_upon_outcome": INTACT_MALE_RX},
            {"breed": {"$in": BREEDS_MOUNTAIN}},
        ]

    elif ft == "disaster":
        base += [
            {"sex_upon_outcome": INTACT_MALE_RX},
            {"age_upon_outcome_in_weeks": {"$gte": 20, "$lte": 300}},
            {"breed": {"$in": BREEDS_DISASTER}},
        ]

    # reset handled by passing {} (see callback)
    return {"$and": base}

# ===== Callbacks =====
@app.callback(Output('datatable-id','data'), [Input('filter-type','value')])
def update_table(filter_type):
    query = {} if filter_type == "reset" else build_query(filter_type)
    return to_df(db.read(query)).to_dict('records')

@app.callback(Output('graph-id',"children"), [Input('datatable-id',"derived_virtual_data")])
def update_chart(viewData):
    dff = pd.DataFrame(viewData) if viewData else df_all.copy()
    if dff.empty or "breed" not in dff:
        return [html.Div("No data to display.")]
    top = dff['breed'].value_counts().nlargest(10).reset_index()
    top.columns = ['breed','count']
    fig = px.bar(top, x='breed', y='count', title='Top Breeds in Current Selection')
    fig.update_layout(xaxis_title="Breed", yaxis_title="Count")
    return [dcc.Graph(figure=fig)]

@app.callback(Output('map-id',"children"),
              [Input('datatable-id',"derived_virtual_data"),
               Input('datatable-id',"derived_virtual_selected_rows")])
def update_map(viewData, selected_rows):
    if not viewData:
        return [html.Div("No records.")]
    dff = pd.DataFrame(viewData)
    row_idx = 0 if not selected_rows else selected_rows[0]
    lat = dff.loc[row_idx].get("location_lat", 30.75)
    lon = dff.loc[row_idx].get("location_long", -97.48)
    breed = dff.loc[row_idx].get("breed","Unknown")
    name = dff.loc[row_idx].get("name","Unknown")
    return [dl.Map(style={'width':'100%','height':'500px'}, center=[lat,lon], zoom=10, children=[
        dl.TileLayer(id="base-layer-id"),
        dl.Marker(position=[lat,lon], children=[
            dl.Tooltip(str(breed)),
            dl.Popup([html.H1("Animal Name"), html.P(str(name))])
        ])
    ])]

# ===== Run inline in Jupyter =====
app.run_server(mode='inline', debug=True)

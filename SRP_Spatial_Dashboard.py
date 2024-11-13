

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Load the current Master Dictionary
master_dict_file = "MasterSRPDictionary.xlsx"
master_df = pd.read_excel(master_dict_file)

# Convert to GeoDataFrame (assuming lat/lon columns exist)
master_gdf = gpd.GeoDataFrame(
    master_df,
    geometry=gpd.points_from_xy(
        master_df["Longitude_or_transect_start_longitude"],
        master_df["Latitude_or_transect_start_latitude"]
    ),
    crs="EPSG:4326"
)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "SRP Spatial Dashboard"

# Layout for the app
app.layout = html.Div([
    # Header with logo and title
    html.Div([
        html.Img(src="https://tpwd.texas.gov/images/responsiveElements/tpwd-logo-large.gif",
                 style={"height": "80px", "margin-right": "15px", "vertical-align": "middle"}),
        html.H1("SRP Spatial Dashboard", style={
            "display": "inline-block",
            "color": "black",  # Title in black
            "font-family": "sans-serif",
            "margin-top": "5px",
            "text-align": "center",
            "vertical-align": "middle"
        })
    ], style={"text-align": "center", "margin-bottom": "10px", "margin-left": "15px"}),

    # Links to external resources
    html.Div([
        html.A("Texas Natural Diversity Database", href="https://tpwd.texas.gov/huntwild/wild/wildlife_diversity/txndd/",
               target="_blank", style={"margin-right": "15px", "font-size": "14px", "color": "#004d99"}),
        html.A("Wildlife Diversity Permits", href="https://tpwd.texas.gov/business/permits/land/wildlife/research/",
               target="_blank", style={"font-size": "14px", "color": "#004d99"})
    ], style={"text-align": "center", "margin-bottom": "10px"}),

    # Filters
    html.Div([
        html.Div([
            html.Label("Filter by SRP Number:", style={"font-weight": "bold", "color": "#004d99"}),
            dcc.Dropdown(
                id="srp-num-filter",
                options=[{"label": srp, "value": srp} for srp in master_df["SRP_Num"].unique()],
                placeholder="Select an SRP Number",
                multi=True,
                style={"font-size": "12px"}
            )
        ], style={"display": "inline-block", "width": "33%", "padding": "0 10px"}),

        html.Div([
            html.Label("Filter by Scientific Name:", style={"font-weight": "bold", "color": "#004d99"}),
            dcc.Dropdown(
                id="scientific-name-filter",
                options=[{"label": sci_name, "value": sci_name} for sci_name in master_df["Scientific_Name"].unique()],
                placeholder="Select a Scientific Name",
                multi=True,
                style={"font-size": "12px"}
            )
        ], style={"display": "inline-block", "width": "33%", "padding": "0 10px"}),

        html.Div([
            html.Label("Filter by Date Range:", style={"font-weight": "bold", "color": "#004d99"}),
            dcc.DatePickerRange(
                id="date-filter",
                start_date=master_df["Observation_Date"].min(),
                end_date=master_df["Observation_Date"].max(),
                display_format="YYYY-MM-DD",
                style={"font-size": "12px"}
            )
        ], style={"display": "inline-block", "width": "33%", "padding": "0 10px"})
    ], style={"margin-bottom": "20px"}),

    # Tabs for different views
    dcc.Tabs([
        dcc.Tab(label="Map View", children=[
            # Record count and download button in the same container
            html.Div([
                html.Div(id="record-count", style={
                    "text-align": "center",
                    "font-weight": "bold",
                    "font-size": "18px",
                    "color": "#004d99",
                    "margin-bottom": "5px"
                }),
                html.Button(
                    "Download Filtered Data",
                    id="download-btn",
                    style={
                        "background-color": "#004d99",
                        "color": "white",
                        "font-weight": "bold",
                        "padding": "12px 24px",
                        "border": "none",
                        "border-radius": "5px",
                        "cursor": "pointer",
                        "font-size": "16px",
                        "margin-top": "10px"
                    }
                ),
                dcc.Download(id="download-data")  # Download component stays here
            ], style={"text-align": "center", "margin-bottom": "15px"}),  # Single container for both Record Count & Download Button
            dcc.Graph(id="spatial-map", style={"height": "60vh"})  # Map display
        ]),

        dcc.Tab(label="Tabular Data View", children=[
            html.Div(id="table-record-count", style={
                "text-align": "center",
                "font-weight": "bold",
                "font-size": "18px",
                "color": "#004d99",
                "margin-bottom": "5px"
            }),
            html.Div(id="table-output", style={
                "margin-top": "10px",
                "font-family": "Arial, sans-serif",
                "overflow-y": "scroll",
                "max-height": "500px",
                "padding": "5px"
            })
        ]),

        dcc.Tab(label="Statistics", children=[
            html.Div(id="statistics-output", style={
                "margin-top": "10px",
                "font-family": "Arial, sans-serif"
            })
        ])
    ])
])

# Callbacks for filtering and updates
@app.callback(
    [Output("spatial-map", "figure"),
     Output("table-output", "children"),
     Output("record-count", "children"),
     Output("table-record-count", "children"),
     Output("statistics-output", "children")],
    [Input("srp-num-filter", "value"),
     Input("scientific-name-filter", "value"),
     Input("date-filter", "start_date"),
     Input("date-filter", "end_date")]
)
def update_views(selected_srp_nums, selected_scientific_names, start_date, end_date):
    filtered_df = master_df.copy()
    if selected_srp_nums:
        filtered_df = filtered_df[filtered_df["SRP_Num"].isin(selected_srp_nums)]
    if selected_scientific_names:
        filtered_df = filtered_df[filtered_df["Scientific_Name"].isin(selected_scientific_names)]
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df["Observation_Date"] >= start_date) &
                                  (filtered_df["Observation_Date"] <= end_date)]

    # Map
    fig_map = px.scatter_mapbox(
        filtered_df,
        lat="Latitude_or_transect_start_latitude",
        lon="Longitude_or_transect_start_longitude",
        hover_data=["SRP_ID", "Scientific_Name", "Common_Name", "County", "SRP_Num"],
        zoom=5,
        mapbox_style="open-street-map"
    )

    # Table
    table = html.Table([
        html.Thead(html.Tr([html.Th(col, style={"padding": "10px"}) for col in filtered_df.columns])),
        html.Tbody([
            html.Tr([html.Td(row[col], style={"padding": "10px"}) for col in filtered_df.columns])
            for _, row in filtered_df.iterrows()
        ])
    ])

    # Record Count
    record_count = f"Record Count: {len(filtered_df)}"

    # Statistics - Record counts by SRP_Num and Scientific_Name
    stats_table = html.Table([
        html.Thead(html.Tr([
            html.Th("Category", style={"padding": "10px"}),
            html.Th("Count", style={"padding": "10px"})
        ])),
        html.Tbody([
            html.Tr([html.Td("SRP Numbers", style={"padding": "10px"}), html.Td(len(filtered_df["SRP_Num"].unique()), style={"padding": "10px"})]),
            html.Tr([html.Td("Scientific Names", style={"padding": "10px"}), html.Td(len(filtered_df["Scientific_Name"].unique()), style={"padding": "10px"})])
        ])
    ])

    return fig_map, table, record_count, record_count, stats_table

# Callback for download button
@app.callback(
    Output("download-data", "data"),
    [Input("download-btn", "n_clicks")],
    [State("srp-num-filter", "value"),
     State("scientific-name-filter", "value"),
     State("date-filter", "start_date"),
     State("date-filter", "end_date")]
)
def download_data(n_clicks, selected_srp_nums, selected_scientific_names, start_date, end_date):
    if not n_clicks:
        return dash.no_update

    # Filter data based on dropdown selections
    filtered_df = master_df.copy()
    if selected_srp_nums:
        filtered_df = filtered_df[filtered_df["SRP_Num"].isin(selected_srp_nums)]
    if selected_scientific_names:
        filtered_df = filtered_df[filtered_df["Scientific_Name"].isin(selected_scientific_names)]
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df["Observation_Date"] >= start_date) &
                                  (filtered_df["Observation_Date"] <= end_date)]

    # Return data for download
    return dcc.send_data_frame(filtered_df.to_csv, "filtered_srp_data.csv", index=False)


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)










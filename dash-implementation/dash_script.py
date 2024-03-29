#### Import Libraries #########
import pandas as pd
import numpy as np
import json
import networkx as nx
import plotly.graph_objects as go
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from datetime import datetime as dt
from stats import *
import pygraphviz as pgv
import dash_bootstrap_components as dbc
### Import functions for Breadth First Search ###

from BFSN import bfs

##### Stylesheet #####
external_stylesheets = [dbc.themes.SANDSTONE]


# Load  Data
df = pd.read_csv('./data/data.csv')
#### Create App ###
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'CDR/IPDR Analyser'
#### Default Variables ####
default_duration_slider_val = [0, 100]
default_time_slider_val = ['00:00', '24:00']
# Loop to generate marks for Time
time_str = ['0', '0', ':', '0', '0']
times = {0: {'label': "".join(time_str), "style": {
    "transform": "rotate(-90deg) translateY(-15px)"}}}
for i in range(0, 48):
    if i % 2 == 0:
        time_str[3] = '3'
        times[i+1] = {'label': "".join(time_str), "style": {'display': 'none'}}
    else:
        time_str = list(
            str(int("".join(time_str[0:2])) + 1).zfill(2) + str(':00'))
        times[i+1] = {'label': "".join(time_str),
                      "style": {"transform": "rotate(-90deg) translateY(-15px)"}}
# Generating marks for duration slider
durations = {}
for i in range(0, df['Duration'].max(), 5):
    durations[i] = str(i)


coords_to_node = {}  # Dictionary that stores coordinates to node number
node_to_num = {}  # Dictionary that stores node number to phone number
data_columns = ["Caller", "Receiver", "Date",
                "Time", "Duration", "TowerID", "IMEI"]
nodes = np.union1d(df['Caller'].unique(), df['Receiver'].unique())  # nodes


# Color scale of edges
viridis = cm.get_cmap('viridis', 12)
# Define Color
df['Dura_color'] = (df['Duration']/df['Duration'].max()).apply(viridis)
df['Date'] = df['Date'].apply(pd.to_datetime).dt.date


df['Caller_node'] = df['Caller'].apply(
    lambda x: list(nodes).index(x))  # Caller Nodes
df['Receiver_node'] = df['Receiver'].apply(lambda x: list(nodes).index(x))
#### Plots ####
# Plot Graph of calls


def plot_network(df):
    G = nx.DiGraph()  # networkX Graph
    # Reciever Nodes

    def make_graph(x):
        G.add_edge(x["Caller_node"], x["Receiver_node"])

    df.apply(make_graph, axis=1)  # Make a graph
    pos = nx.nx_agraph.graphviz_layout(G)  # Position of Points

    # Add Edges to Plot
    edge_trace = []

    def add_coords(x):
        x0, y0 = pos[x['Caller_node']]
        x1, y1 = pos[x['Receiver_node']]

        node_to_num[x['Caller_node']] = x['Caller']
        node_to_num[x['Receiver_node']] = x['Receiver']
        edge_trace.append(dict(type='scatter',
                               x=[x0, x1], y=[y0, y1],
                               line=dict(
                                   width=0.5, color='rgba'+str(x['Dura_color']).replace(']', ')').replace('[', '(')),
                               hoverinfo='none',
                               mode='lines'))  # Graph object for each connection

    df.apply(add_coords, axis=1)  # Adding edges

    # adding points
    node_x = []
    node_y = []
    for node in pos:
        x, y = pos[node]
        coords_to_node[(x, y)] = node
        node_x.append(x)
        node_y.append(y)
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            size=10,
            line_width=2))  # Object for point scatter plot
    fig = go.Figure(data=edge_trace+[node_trace],
                    layout=go.Layout(
                   
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    annotations=[dict(
                        showarrow=True,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002)],
                    xaxis=dict(showgrid=False, zeroline=False,
                               showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )  # Complete Figure

    fig.update_layout(transition_duration=500)  # Transition
    fig.update_layout(clickmode='event+select')  # Event method

    fig.update_traces(marker_size=20)  # marker size
    return fig

# Create an image for the same. -- What?


##### Layout of App #####
app.layout = html.Div(children=[
    html.Div(children=[
        html.H1(children='CDR Analyser'),  # Title
        html.H3(children='''
        Analyse the phone calls between people.
    '''),  # Subtitle
        html.Div(
            id='date-selected'
        ),  # Date Selected Indicator
        html.H4(id='message'),  # Message
    ],id='header-text'),

    dbc.Row(children=[
        dbc.Col(children=[
            html.H3(
                'Filters'
            ),
            html.H5(
                'Date:'
            ),
            dcc.DatePickerSingle(
                id='date-picker',
                min_date_allowed=df['Date'].min(),
                max_date_allowed=df['Date'].max(),
                initial_visible_month=dt(2020, 6, 5),
                date=str(dt(2020, 6, 17, 0, 0, 0))
            ),  # Data Picker
            dcc.RangeSlider(
                id='duration-slider',
                min=0,
                max=df['Duration'].max(),
                step=None,
                marks=durations,

                value=default_duration_slider_val,
                dots=True,

            ),  # Duration Slider

            dcc.RangeSlider(
                id='time-slider',
                min=0,
                max=48,
                step=None,
                marks=times,
                dots=True,
                value=[0, 48],
                pushable=1

            ),  # Time Slider
            html.H5(
                'Condition for Caller/Reciever'
            ),
            dcc.Dropdown(
                id='select-caller-receiver',
                options=[{'label': 'Only Caller', 'value': 1}]+[{'label': 'Only Receiver', 'value': 2}]+[
                    {'label': 'Either Caller or Reciever', 'value': 3}]+[{'label': 'Both Caller and Reciever', 'value': 4}],
                value=3,
            ),  # Select if you want the select the numbers to be from Caller/Reciever/Both/Either
           
            html.H5(
                'Select Caller:'
            ),
            dcc.Dropdown(
                id='caller-dropdown',
                options=[{'label': 'None', 'value': 'None'}] + \
                [{'label': k, 'value': k} for k in df['Caller'].unique()],
                value='None',
                multi=True,
            ),  # Dropdown for Caller
            html.H5(
                'Select Reciever:'
            ),
            dcc.Dropdown(
                id='receiver-dropdown',
                options=[{'label': 'None', 'value': 'None'}] + \
                [{'label': k, 'value': k} for k in df['Receiver'].unique()],
                value='None',
                multi=True,
            )],  # Dropdown for Reciever,
            id='filters',lg=3),  # Filters
        dbc.Col(
           [ html.H3('Network Graph : '),
            dcc.Graph(
                id='network-plot'

            )],id='plot-area',lg=6),     # Network Plot
        dbc.Col(children=[
            html.H3('Statistics'),
            html.Div([
                dcc.Markdown("""
                **Hover To Get Stats** \n
                Mouse over nodes in the graph to get statistics.
            """),
                html.Pre(id='hover-data',)
            ],),  # Hover Data Container

            html.Div([
                
                dcc.Markdown("""
                **Click to get CDR for a number** \n
                Click on points in the graph to get the call data records.
            """),
                html.Pre(id='click-data', ),
            ], ),  # Click Data Container

            html.Div([
                dcc.Markdown("""
                **Select to see connected people** \n
                Select using rectangle/lasso or by using your mouse.(Use Shift for multiple selections)
            """),
                html.Pre(id='selected-data', ),
            ], )  # Selection Data Container


        ],id='stats',lg=3)

    ],className='container-mid'),
    html.Div(
        id='filtered-data',
        style={'display': 'none'}
    ),
    # Filtered Data
])

#### Callbacks ####
# Callback to update df used for plotting
# Callback to filter dataframe
# REMEMBER WHILE EDITING (RWI): THIS IS A TWO OUTPUT FUNCTION


@app.callback(
    [Output(component_id='filtered-data', component_property='children'),
     Output(component_id='message', component_property='children')],
    [Input(component_id='date-picker', component_property='date'), Input(component_id='duration-slider', component_property='value'), Input(component_id='time-slider', component_property='value'),
     Input(component_id='select-caller-receiver', component_property='value'), Input(component_id='caller-dropdown', component_property='value'), Input(component_id='receiver-dropdown', component_property='value')]
)
def update_filtered_div_caller(selected_date, selected_duration, selected_time, selected_option, selected_caller, selected_receiver):
    # Date,Time,Duration Filter

    filtered_df = df[(df['Date'] == pd.to_datetime(selected_date))
                     & ((df['Duration'] >= selected_duration[0]) & (df['Duration'] <= selected_duration[1]))
                     & ((df['Time'] < times[selected_time[1]]['label']) & (df['Time'] >= times[selected_time[0]]['label']))].reset_index(drop=True)

    # Number Filter
    # If Caller is Selected
    if(selected_option == 1):
        if selected_caller != 'None':
            filtered_df = filtered_df[(filtered_df['Caller'].isin(
                list(selected_caller)))].reset_index(drop=True)
   # If Receiver is selected
    if(selected_option == 2):
        if selected_receiver != 'None':
            filtered_df = filtered_df[(filtered_df['Receiver'].isin(
                (selected_receiver)))].reset_index(drop=True)
   # If the option either is selected
    if(selected_option == 3):
        if selected_caller != 'None' or selected_receiver != 'None':
            filtered_df = filtered_df[((filtered_df['Caller'].isin(list(selected_caller))) | (
                filtered_df['Receiver'].isin(list(selected_receiver))))].reset_index(drop=True)
    # If option both is selected
    if(selected_option == 4):
        if selected_caller != 'None' and selected_receiver != 'None':
            filtered_df = df[((filtered_df['Caller'].isin(list(selected_caller))) & (
                filtered_df['Receiver'].isin(list(selected_receiver))))].reset_index(drop=True)
    if filtered_df.shape[0] == 0:
        # No update since nothing matches
        return dash.no_update, 'Nothing Matches that Query'
    else:
        # Update Filtered Dataframe
        return filtered_df.to_json(date_format='iso', orient='split'), 'Updated'
# Callback for hover data
# Display Stats in hoverdata


@app.callback(
    Output('hover-data', 'children'),
    [Input('network-plot', 'hoverData'), Input(component_id='filtered-data', component_property='children')])
def display_hover_data(hoverData, filtered_data):

    df = pd.read_json(filtered_data, orient='split')
    if hoverData is not None:
        # Get node number corresponding to the point.

        nodeNumber = coords_to_node[(
            hoverData['points'][0]['x'], hoverData['points'][0]['y'])]
        hd = 'Selected Number: ' + \
            str(node_to_num[nodeNumber]) + '\n'  # hd: Hover Data string

        # Functions are from stats.py
        hd += "Mean Duration : " + str(meanDur(nodeNumber, df)) + "\n"
        hd += "Peak Hours(duration):\n"
        m = peakHours(nodeNumber, df)
        for x in m:
            hd += "\t\t  " + str(x)+"-"+str(x+1)+" : "+str(m[x])+"\n"
        z = ogIc(nodeNumber, df)  # Outgoing Incoming
        hd += "No. of Outgoing Calls: " + str(z[0])+"\n"
        hd += "No. of Incomming Calls: " + str(z[1])+"\n"
        z = mostCalls(nodeNumber, df)  # Most Calls
        hd += "Most Calls to: " + str(z[0]) + "\n"
        hd += "Most Calls from: " + str(z[1]) + "\n"
        hd += "Most Calls: " + str(z[2]) + "\n"
        return hd
    return "Hover data..."

# Callback for Network Plot
# Show table for the clicked phone number


@app.callback(
    Output('click-data', 'children'),
    [Input('network-plot', 'clickData')])
def display_click_data(clickData):
    if clickData is not None:
        nodeNumber = coords_to_node[(
            clickData['points'][0]['x'], clickData['points'][0]['y'])]
        # Filtering DF
        return df[(df['Caller_node'] == nodeNumber) | (df['Receiver_node'] == nodeNumber)][data_columns].to_string(index=False)
    return "Click on a node to view more data"


# Callback for Selected Data
@app.callback(
    Output('selected-data', 'children'),
    [Input('network-plot', 'selectedData'), Input(component_id='filtered-data', component_property='children')])
def display_selected_data(selectedData, filtered_data):
    df = pd.read_json(filtered_data, orient='split')
    # TODO #3 Graph should also be filtered and only nodes in component should be displayed
    if selectedData is not None:
        l = []
        for point in selectedData['points']:
            l.append(node_to_num[coords_to_node[point['x'], point['y']]])
        components = bfs(l, df)
        s = ""
        i = 1
        for component in components:
            if not component:
                continue
            s += "Component "+str(i)+":\n"
            i += 1
            for number in component:
                s += "\t" + str(number) + "\n"
        return s
    return json.dumps(selectedData, indent=2)


# Callback to update network plot
@app.callback(
    Output(component_id='network-plot', component_property='figure'),
    [Input(component_id='filtered-data', component_property='children')]
)
def update_network_plot_caller(filtered_data):
    return plot_network(pd.read_json(filtered_data, orient='split'))

# TODO UPDATE THESE CALLBACKS TO INCLUDE TIME AND DURATION UPDATES
# Callback to change selectors including caller no. according to date


@app.callback(
    Output(component_id='caller-dropdown', component_property='options'),
    [Input(component_id='date-picker', component_property='date')]
)
def update_phone_div_caller(selected_date):
    return [{'label': 'None', 'value': ''}]+[{'label': k, 'value': k} for k in df[df['Date'] == pd.to_datetime(selected_date)]['Caller'].unique()]

# Callback to change reciever according  to dates


@app.callback(
    Output(component_id='receiver-dropdown', component_property='options'),
    [Input(component_id='date-picker', component_property='date')]
)
def update_phone_div_receiver(selected_date):
    return [{'label': 'None', 'value': ''}]+[{'label': k, 'value': k} for k in df[df['Date'] == pd.to_datetime(selected_date)]['Receiver'].unique()]


#### Run Server ####
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')

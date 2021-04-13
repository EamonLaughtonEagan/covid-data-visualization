import json
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from addEdge import addEdge

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


# style settings
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

# SCHEMA: CASE_ID, LINKED_CASES, REPORT_DATE, LOCATION, PERSONAL_INFORMATION
# LINKED_CASES: CASE 1, ..., CASE N
# PERSONAL_INFORMATION: FIRST_NAME, LAST_NAME
with open('Singapore_Data.json') as f:
    data = json.load(f)

# cleaning up the database
df = pd.json_normalize(data['DATA'])
#df = df[0:101]
clusters = []
cluster_names = []

df_cluster = pd.json_normalize(data['CLUSTER'])
for i in range(len(df_cluster)):
    for j in range(len(df_cluster['CASE_IDS'][i])):
        clusters.append(df_cluster['CASE_IDS'][i][j])
    cluster_names.append(df_cluster['LOCATION'][i])


#create a column in the data frame for the length each linked case for each case
len_linked_cases = []
for i in range(len(df)):
    length = 0
    for j in range(len(df['LINKED_CASES'][i])):
        length += 1
    len_linked_cases.append(length)
df['LEN_LINKED_CASES'] = len_linked_cases

#adding additional data to the datafram to be displayed in the network graph
dates = []
unique_dates = []
size = []
for i in range(len(df)):
    dates.append(df['REPORT_DATE.MONTH'][i] + ' ' + str(df['REPORT_DATE.DAY'][i]))
    if df['EXPOSURE'][i] == 'IMPORTED' and df['LEN_LINKED_CASES'][i] > 0:
        size.append(0.5)
    else:
        size.append(0.1)

    

df['DATE'] = dates
df['SIZE'] = size

for i in range(len(df)):
    if dates[i] not in unique_dates:
        unique_dates.append(dates[i])
    else:
        unique_dates.append(' ')
df['UNIQUE_DATE'] = unique_dates

#creating the tree-like graph layout for the nodes
y_positions = []
for i in range(len(df)):
    if df['LOCATION'][i] in cluster_names and df['EXPOSURE'][i] == 'IMPORTED':
        y_positions.append(60)
    elif df['LOCATION'][i] in cluster_names and df['EXPOSURE'][i] == 'LOCAL':
        y_positions.append(50) 
    elif df['LINKED_CASES'][i] != [] and df['EXPOSURE'][i] == 'IMPORTED':
        y_positions.append(40)
    elif df['LINKED_CASES'][i] != [] and df['EXPOSURE'][i] == 'LOCAL':
        y_positions.append(30)
    elif df['LINKED_CASES'][i] == [] and df['EXPOSURE'][i] == 'LOCAL':
        y_positions.append(20)
    elif df['LINKED_CASES'][i] == [] and df['EXPOSURE'][i] == 'IMPORTED':
        y_positions.append(10)
    elif df['EXPOSURE'][i] == '' and df['LOCATION'][i] == '':
        y_positions.append(0)
    else:
        y_positions.append(10)
df['Y_POSITIONS'] = y_positions





fig = go.Figure()
fig.update_layout(
    autosize=False,
    hovermode='closest',
    margin=dict(b=5, l=40, r=5, t=50),
    annotations=[dict(showarrow=False, xref="paper", yref="paper", x=0.005, y=- 0.002)],
    yaxis=dict(title=''),
    xaxis=dict(title=''),
    legend=dict(x=1, y=1, title_text='Locations', bordercolor='black', borderwidth=2, itemclick='toggleothers'),

    clickmode='event+select',
)

app.layout = html.Div([
    html.H1('Singapore Data Visualization'),
    html.P(
        'Graph indicating unique cases and their respective connections throughout the begining months of the COVID-19 pandemic in 2020.'),
    dcc.Graph(id='main-graph'),
    html.P('Selected Date(s)'),
    dcc.RangeSlider(
        id='range-slider',
        min=0, max=len(df)-1, step=1,
        marks={
            0: str(df['REPORT_DATE.MONTH'][0]) + ' ' + str(df['REPORT_DATE.DAY'][0]),
            len(df) / 2: str(df['REPORT_DATE.MONTH'][(len(df) - 1) / 2]) + ' ' + str(df['REPORT_DATE.DAY'][(len(df) - 1) / 2]),
            len(df)-1: str(df['REPORT_DATE.MONTH'][len(df)-1]) + ' ' + str(df['REPORT_DATE.DAY'][len(df)-1])},
        value=[0, 50]
    ),
    html.Div(children=[
        html.H2('Current range of Dates'),
        html.H3(id='range-of-dates')
    ]),
    html.Div(children=[
        html.H4('Cluster Data'),
        html.H5(id='hover-data', style=styles['pre'])
    ]),
])


@app.callback(
    Output('main-graph', 'figure'),
    Input('range-slider', 'value'))
def update_graph(slider_range):

    dff = df
    low, high = slider_range
    mask = (dff['CASE_ID'] > low) & (dff['CASE_ID'] < high)
    
    #adding the 'nodes' of the graph
    fig = px.scatter(
        dff[mask], x='CASE_ID', y='Y_POSITIONS', custom_data=['CASE_ID', 'LINKED_CASES', 'EXPOSURE', 'LOCATION', 'DATE'],
        color='LOCATION', size='SIZE', height=500, width=1500,
        hover_data=['LINKED_CASES'])
    fig.update_layout(
        xaxis=dict(
            title='DATE', 
            showticklabels=True,
            tickmode='array',
            tickvals=dff['CASE_ID'],
            ticktext=dff['UNIQUE_DATE'],
            tickfont_size=10,
            showgrid=False,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            color='black',
            linecolor='black',
            mirror=True),
        yaxis=dict(
            title='',
            tickmode='array',
            tickvals=[0, 10, 20, 30, 40, 50, 60],
            ticktext=['OTHER', 'IMPORTED', 'LOCAL', 'LOCAL W/ CONNECTIONS', 'IMPORTED W/ CONNECTIONS', 'LOCAL IN CLUSTER', 'IMPORTED IN CLUSTER'],
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            zeroline=False,
            color='black',
            linecolor='black',
            mirror=True))

    fig.update_traces(
        hovertemplate='<br>'.join([
            'Case ID: %{customdata[0]}',
            'Linked Cases: %{customdata[1]}',
            'Exposure: %{customdata[2]}',
            'Location: %{customdata[3]}',
            'Date:  %{customdata[4]}'
        ]))

    '''
    for i in range(low, high): # 0 - 50
        if dff['LINKED_CASES'][i] != [] and dff['EXPOSURE'][i] == 'IMPORTED':
            for j in range(len(dff['LINKED_CASES'][i])): # 1 - length of linked case
                if dff['LINKED_CASES'][i][j] > low+1 and dff['LINKED_CASES'][i][j] < high-1:
                    line = go.Scatter(
                        x=[dff['CASE_ID'][i], dff['LINKED_CASES'][i][j]], 
                        y=[dff['Y_POSITIONS'][i], dff['Y_POSITIONS'][dff['LINKED_CASES'][i][j]-1]],
                        showlegend=False,
                        mode='lines',
                        line=go.scatter.Line(color='gray', dash='dot'))
                    fig.add_trace(line)
    '''

    #Adding the arrows to the graph that act as edges
    for i in range(low, high): # 0 - 50
        if dff['LINKED_CASES'][i] != [] and dff['EXPOSURE'][i] == 'IMPORTED':
            for j in range(len(dff['LINKED_CASES'][i])): # 1 - length of linked case
                if dff['LINKED_CASES'][i][j] > low+1 and dff['LINKED_CASES'][i][j] < high-1:
                    arrow = go.layout.Annotation(dict(
                        #starting coordinates
                        ax=dff['CASE_ID'][i], ay=dff['Y_POSITIONS'][i],
                        axref = 'x', ayref='y',

                        #eding coordinates
                        x=dff['LINKED_CASES'][i][j], y=dff['Y_POSITIONS'][dff['LINKED_CASES'][i][j]-1],
                        xref='x', yref='y', 
                        arrowhead=3, 
                        arrowwidth=1,
                        showarrow=True))
                    fig.add_annotation(arrow)
    """
    arrow = go.layout.Annotation(dict(
        #starting coordinates
        ax=dff['CASE_ID'][1], ay=dff['Y_POSITIONS'][1],
        axref = 'x', ayref='y',

        #eding coordinates
        x=dff['CASE_ID'][2], y=dff['Y_POSITIONS'][2],
        xref='x', yref='y', 
        arrowhead=3, 
        arrowwidth=1,
        showarrow=True))
    fig.add_annotation(arrow)
    """
    return fig
 

@app.callback(
    Output('range-of-dates', 'children'),
    Input('range-slider', 'value'))
def update_dates(slider_range):
    low, high = slider_range
    container = df['REPORT_DATE.MONTH'][low] + ' ' + str(df['REPORT_DATE.DAY'][low]) + ' - ' + df['REPORT_DATE.MONTH'][high] + ' ' + str(df['REPORT_DATE.DAY'][high])
    return container


@app.callback(
    Output('hover-data', 'children'),
    Input('main-graph', 'hoverData'))
def show_cluster(hover_data):
    try:
        case_id = hover_data['points'][0]['customdata'][0]
        linked_cases = hover_data['points'][0]['customdata'][1]
        exposure = hover_data['points'][0]['customdata'][2]
        is_cluster = hover_data['points'][0]['customdata'][3]
        if is_cluster in cluster_names:
            return 'Case number: ' + str(case_id) + ' is part of the following cluster: ' + str(is_cluster)
        elif case_id in clusters:
            return 'Case number: ' + str(case_id) + ' is associated with the following cases: ' + str(linked_cases)
        else:
            return 'Case is not part of a cluster'
    except TypeError:
        pass

app.run_server(debug=True)
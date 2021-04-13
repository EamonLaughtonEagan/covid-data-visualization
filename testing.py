import plotly.graph_objects as go
import networkx as nx
import dash
import dash_core_components as dcc
import dash_html_components as html
import json
import pandas as pd
import random
from addEdge import addEdge

with open('Singapore_Data.json') as f:
    data = json.load(f)
df = pd.json_normalize(data['DATA'])
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

#display dates as MONTH + DAY
dates = []
for i in range(len(df)):
    dates.append(df['REPORT_DATE.MONTH'][i] + ' ' + str(df['REPORT_DATE.DAY'][i]))
df['DATE'] = dates


#creating the tree-like graph layout for the nodes
y_positions = []
for i in range(len(df)):
    if df['LINKED_CASES'][i] == [] and df['EXPOSURE'][i] == 'LOCAL': 
        y_positions.append(random.randint(1, 5))
    elif df['LINKED_CASES'][i] == [] and df['EXPOSURE'][i] == 'IMPORT':
        y_positions.append(random.randint(6, 10))
    elif len(df['LINKED_CASES'][i]) <= 10 and len(df['LINKED_CASES'][i]) >= 0 and df['EXPOSURE'][i] == 'LOCAL':
        y_positions.append(random.randint(15, 20))
    elif len(df['LINKED_CASES'][i]) <= 10 and len(df['LINKED_CASES'][i]) >= 0 and df['EXPOSURE'][i] == 'IMPORT':
        y_positions.append(random.randint(21, 25))
    elif len(df['LINKED_CASES'][i]) > 10:
        y_positions.append(random.randint(26, 30))
    else:
        y_positions.append(-10)
df['Y_POSITIONS'] = y_positions





# Controls for how the graph is drawn
nodeColor = 'Red'
nodeSize = 10
lineWidth = 2
lineColor = '#000000'

# Make a random graph using networkx
G = nx.random_geometric_graph(5, .5)
pos = nx.layout.spring_layout(G)
for node in G.nodes:
    G.nodes[node]['pos'] = list(pos[node])
    
# Make list of nodes for plotly
node_x = []
node_y = []
for node in G.nodes():
    x, y = G.nodes[node]['pos']
    node_x.append(x)
    node_y.append(y)

    
# Make a list of edges for plotly, including line segments that result in arrowheads
edge_x = []
edge_y = []
for edge in G.edges():
    # addEdge(start, end, edge_x, edge_y, lengthFrac=1, arrowPos = None, arrowLength=0.025, arrowAngle = 30, dotSize=20)
    start = G.nodes[edge[0]]['pos']
    print(start)
    end = G.nodes[edge[1]]['pos']
    print(end)
    print('\n')
    edge_x, edge_y = addEdge(start, end, edge_x, edge_y, .8, 'end', .04, 30, nodeSize)

edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=lineWidth, color=lineColor), hoverinfo='none', mode='lines')

node_trace = go.Scatter(x=node_x, y=node_y, mode='markers', hoverinfo='text', marker=dict(showscale=False, color = nodeColor, size=nodeSize))

fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
             
# Note: if you don't use fixed ratio axes, the arrows won't be symmetrical
fig.update_layout(yaxis = dict(scaleanchor = "x", scaleratio = 1), plot_bgcolor='rgb(255,255,255)')
    
app = dash.Dash()
app.layout = html.Div([dcc.Graph(figure=fig)])

app.run_server(debug=True)
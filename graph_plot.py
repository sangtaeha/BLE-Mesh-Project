import igraph as ig
import json
import urllib3
import plotly as py
import plotly.graph_objs as go

data = []
f=open("/home/matsy007/Downloads/Mesh/BLE-Mesh-Project/Mesh_demo.json","r")
data=json.load(f)

N = len(data)

Edges=[]
for i in range(N):
    for j in range(N):
        Edges.append([i, j])

G=ig.Graph(Edges, directed=False)

group = []
labels = []
for item in data:
    group.append(int(item["Group_ID"]))
    labels.append(item["Name"])

layt=G.layout('kk', dim=3)

Xn=[layt[k][0] for k in range(N)]# x-coordinates of nodes
Yn=[layt[k][1] for k in range(N)]# y-coordinates
Zn=[layt[k][2] for k in range(N)]# z-coordinates
Xe=[]
Ye=[]
Ze=[]
for e in Edges:
    Xe+=[layt[e[0]][0],layt[e[1]][0], None]# x-coordinates of edge ends
    Ye+=[layt[e[0]][1],layt[e[1]][1], None]
    Ze+=[layt[e[0]][2],layt[e[1]][2], None]

trace1=go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color='rgb(125,125,125)', width=1), hoverinfo='none')
trace2=go.Scatter3d(x=Xn, y=Yn, z=Zn, mode='markers', name='Mesh Nodes', marker=dict(symbol='circle', 
        size=6, color=group, colorscale='Viridis', 
        line=dict(color='rgb(50,50,50)', width=0.5)), 
        text=labels, hoverinfo='text')
axis=dict(showbackground=False, showline=False, zeroline=False, showgrid=False, showticklabels=False, title='' )

layout = go.Layout(
         title="3D visulization of Mesh Network",
         width=1000,
         height=1000,
         showlegend=False,
         scene=dict(
             xaxis=dict(axis),
             yaxis=dict(axis),
             zaxis=dict(axis),
        ),
     margin=dict(
        t=100
    ),
    hovermode='closest',
    annotations=[
           dict(
           showarrow=False,
            text="",
            xref='paper',
            yref='paper',
            x=0,
            y=0.1,
            xanchor='left',
            yanchor='bottom',
            font=dict(
            size=14
            )
            )
        ],    )

data=[trace1, trace2]
fig=go.Figure(data=data, layout=layout)


js_str = py.offline.plot(fig, include_plotlyjs=False, output_type='div')

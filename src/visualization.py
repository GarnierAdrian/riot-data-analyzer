import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.read_csv("data/interm/game.csv")

fig = px.bar(df, x="role", y="stats.kills", color="teamName", barmode="stack")

df2 = pd.read_csv("data/interm/player_frames.csv")
fig2 = px.scatter(df2, width=1000, height=1000, animation_frame='timestamps', x='position_x', y='position_y', color='summonerName')
fig2.add_layout_image(
    dict(
            source=r"https://vignette.wikia.nocookie.net/leagueoflegends/images/0/04/Summoner's_Rift_Minimap.png/revision/latest?cb=20170222210641",
            xref="x",
            yref="y",
            x=0,
            y=15000,
            sizex=15000,
            sizey=15000,
            sizing="stretch",
            opacity=1,
            layer="below")
)




app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),
    generate_table(df),
    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
    dcc.Graph(
        id='example-graph-scatter-plot',
        figure=fig2
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
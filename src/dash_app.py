from datetime import date

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import plotly.graph_objects as go

# Make a Dash app!
from src.backtest import backtest

app = dash.Dash(__name__)

# Define the layout.
app.layout = html.Div([
    html.H1("Strategy Backtest on IVV, Minglun & Yajie"),
    html.Div([
        html.P("Range of Date"),
        dcc.DatePickerRange(
            id='date_ranger',
            min_date_allowed=date(2015, 4, 12),
            max_date_allowed=date(2021, 4, 12),
            initial_visible_month=date(2021, 4, 12),
            start_date=date(2015, 4, 12),
            end_date=date(2021, 4, 12)
        )
    ],
        style={"margin-right": "15px"}
    ),
    html.Br(),
    html.Div([
        html.P("Range of short term n: "),
        dcc.RangeSlider(
            id='small_n_range',
            min=1,
            max=10,
            step=1,
            value=[5, 7],
            marks={str(i): {'label': str(i)} for i in range(1, 11)}
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div([
        html.P("Range of long term n: "),
        dcc.RangeSlider(
            id='large_n_range',
            min=11,
            max=20,
            step=1,
            value=[10, 13],
            marks={str(i): {'label': str(i)} for i in range(11, 21)}
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div([
        html.P("Percent of Buy: "),
        dcc.Input(
            type='number',
            id='buy_percent',
            value=0.5,
            min=0.0,
            max=1.0,
            step=0.01
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div([
        html.P("Percent of Sell: "),
        dcc.Input(
            type='number',
            id='sell_percent',
            value=0.5,
            min=0.0,
            max=1.0,
            step=0.01
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div([
        html.P("Buy signal strength: "),
        dcc.Input(
            type='number',
            id='buy_signal_strength',
            value=0,
            min=0,
            max=5,
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div([
        html.P("Sell signal strength: "),
        dcc.Input(
            type='number',
            id='sell_signal_strength',
            value=0,
            min=0,
            max=5,
        )
    ],
        style={"width": "30%"}),
    html.Br(),
    html.Div(html.Button('Back Test', id='submit-button', n_clicks=0)),
    html.Br(),
    html.Div([
        html.H2("IVV Price"),
        dcc.Graph(id='graph_ivv')
    ]),
    html.Br(),
    html.Div([
        html.H2("Our Strategy Value"),
        dcc.Graph(id='graph_strategy')
    ]),
    html.Br(),
    html.Div([
        html.H2("Linear Regression"),
        dcc.Graph(id='linear_regression')
    ]),
    html.Br(),
    html.Div([
        html.H2("All indexes"),
        dash_table.DataTable(id='indexes', page_size=1)
    ]),
    html.Br(),
    html.Div([
        html.H2("Trade Blotter"),
        dash_table.DataTable(id='blotter', page_size=10)
    ]),
    html.Br(),
    html.Div([
        html.H2("Trade Ledger"),
        dash_table.DataTable(id='ledger', page_size=10)
    ]),
    html.Br(),
    html.Br(),
])


@app.callback(
    [dash.dependencies.Output('graph_ivv', 'figure'),
     dash.dependencies.Output('graph_strategy', 'figure'),
     dash.dependencies.Output('linear_regression', 'figure'),
     dash.dependencies.Output('blotter', 'data'),
     dash.dependencies.Output('blotter', 'columns'),
     dash.dependencies.Output('ledger', 'data'),
     dash.dependencies.Output('ledger', 'columns'),
     dash.dependencies.Output('indexes', 'data'),
     dash.dependencies.Output('indexes', 'columns')],
    dash.dependencies.Input('submit-button', 'n_clicks'),
    [dash.dependencies.State('date_ranger', 'start_date'),
     dash.dependencies.State('date_ranger', 'end_date'),
     dash.dependencies.State('small_n_range', 'value'),
     dash.dependencies.State('large_n_range', 'value'),
     dash.dependencies.State('buy_percent', 'value'),
     dash.dependencies.State('sell_percent', 'value'),
     dash.dependencies.State('buy_signal_strength', 'value'),
     dash.dependencies.State('sell_signal_strength', 'value')],
    prevent_initial_call=True
)
def show_graph(n_clicks, start_date, end_date, small_n, large_n, buy_p, sell_p, bss, sss):
    blotter, ledger, indexes = backtest(start_date, end_date, small_n[0], small_n[1], large_n[0], large_n[1], buy_p,
                                        sell_p, bss, sss)
    fig_ivv = px.line(x=ledger['date'], y=ledger['ivv_price'], labels={'x': "date", 'y': "ivv_price"})
    fig_strategy = px.line(x=ledger['date'], y=ledger['portfolio_value'], labels={'x': "date", 'y': "portfolio_value"})
    blot_columns = [{"name": i, "id": i} for i in blotter.columns]
    blot_data = blotter.to_dict('records')
    ledger_columns = [{"name": i, "id": i} for i in ledger.columns]
    ledger_data = ledger.to_dict('records')
    indexes_columns = [{"name": i, "id": i} for i in indexes.columns]
    indexes_data = indexes.to_dict('records')
    x = ledger['ivv_price_change'].tolist()
    y = ledger['portfolio_price_change'].tolist()
    df = pd.DataFrame({'x': x, 'y': y})
    reg = LinearRegression().fit(np.vstack(df['x']), y)
    df['bestfit'] = reg.predict(np.vstack(df['x']))
    fig_linear = go.Figure()
    fig_linear.add_trace(go.Scatter(name='IVV vs Portfolio', x=df['x'], y=df['y'].values, mode='markers'))
    fig_linear.add_trace(go.Scatter(name='line of best fit', x=x, y=df['bestfit'], mode='lines'))
    fig_linear.update_layout(xaxis_title='IVV', yaxis_title='Portfolio')
    return fig_ivv, fig_strategy, fig_linear, blot_data, blot_columns, ledger_data, ledger_columns, indexes_data, indexes_columns


if __name__ == '__main__':
    app.run_server(debug=True)

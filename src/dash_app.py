from datetime import date

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

# Make a Dash app!
from src.backtest import backtest

app = dash.Dash(__name__)

# Define the layout.
app.layout = html.Div([
    html.H1("Strategy Backtest on IVV, Minglun & Yajie"),
    html.Div(
        dcc.DatePickerRange(
            id='date_ranger',
            min_date_allowed=date(2015, 4, 12),
            max_date_allowed=date(2021, 4, 12),
            initial_visible_month=date(2021, 4, 12),
            start_date=date(2015, 4, 12),
            end_date=date(2021, 4, 12)
        ),
        style={'display': 'inline-block', "margin-right": "15px"}
    ),

    html.Div(
        html.Button('Back Test', id='submit-button', n_clicks=0)
        , style={'display': 'inline-block'}),
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
        html.H2("Trade Blotter"),
        dash_table.DataTable(id='blotter', page_size=10)
    ]),
    html.Br(),
    html.Div([
        html.H2("Trade Ledger"),
        dash_table.DataTable(id='ledger', page_size=10)
    ]),
    html.Br(),
    html.Div([
    html.H2("All indexes"),
        dash_table.DataTable(id='indexes', page_size=1)
    ]),
    html.Br(),
    html.Br(),
])


@app.callback(
    [dash.dependencies.Output('graph_ivv', 'figure'),
     dash.dependencies.Output('graph_strategy', 'figure'),
     dash.dependencies.Output('blotter', 'data'),
     dash.dependencies.Output('blotter', 'columns'),
     dash.dependencies.Output('ledger', 'data'),
     dash.dependencies.Output('ledger', 'columns'),
     dash.dependencies.Output('indexes', 'data'),
     dash.dependencies.Output('indexes', 'columns')],
    dash.dependencies.Input('submit-button', 'n_clicks'),
    [dash.dependencies.State('date_ranger', 'start_date'),
     dash.dependencies.State('date_ranger', 'end_date')],
    prevent_initial_call=True
)
def show_graph(n_clicks, start_date, end_date):
    blotter, ledger, indexes = backtest(start_date, end_date)
    fig_ivv = px.line(x=ledger['date'], y=ledger['ivv_price'], labels={'x': "date", 'y': "ivv_price"})
    fig_strategy = px.line(x=ledger['date'], y=ledger['portfolio_value'], labels={'x': "date", 'y': "portfolio_value"})
    blot_columns = [{"name": i, "id": i} for i in blotter.columns]
    blot_data = blotter.to_dict('records')
    ledger_columns = [{"name": i, "id": i} for i in ledger.columns]
    ledger_data = ledger.to_dict('records')
    indexes_columns = [{"name": i, "id": i} for i in indexes.columns]
    indexes_data = indexes.to_dict('records')
    return fig_ivv, fig_strategy, blot_data, blot_columns, ledger_data, ledger_columns, indexes_data, indexes_columns


if __name__ == '__main__':
    app.run_server(debug=True)

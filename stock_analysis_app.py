import os
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Initialize Dash App
app = Dash(__name__)
server = app.server  # Required for Render deployment

default_stocks = ["RELIANCE.NS", "TCS.NS"]

def fetch_data():
    nifty50_stocks = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "BAJFINANCE.NS", "HCLTECH.NS", "LT.NS", "SBIN.NS", "ASIANPAINT.NS"
    ]
    try:
        df = yf.download(nifty50_stocks, start="2020-01-01", end="2024-12-31")["Close"].dropna()
        returns_df = df.pct_change().dropna()
        roi = returns_df.mean() * 252
        volatility = returns_df.std() * np.sqrt(252)
        performance_df = pd.DataFrame({'Stock': roi.index, 'ROI': roi.values, 'Volatility': volatility.values})
        return df, returns_df, performance_df
    except Exception as e:
        print("Error fetching data:", e)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, returns_df, performance_df = fetch_data()

app.layout = html.Div([
    html.H1("Stock Investment Analysis"),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': stock, 'value': stock} for stock in performance_df['Stock']],
        multi=True,
        value=default_stocks
    ),
    html.Div(id='graph-container')
])

@app.callback(
    Output('graph-container', 'children'),
    Input('stock-dropdown', 'value')
)
def update_graphs(selected_stocks):
    graphs = []
    if df.empty or performance_df.empty:
        return [html.P("No data available. Please check back later.")]
    
    # Risk-Return Graph
    fig1 = px.scatter(performance_df, x='Volatility', y='ROI', text='Stock', title="Risk vs Return")
    graphs.append(dcc.Graph(figure=fig1))
    
    # Historical Trends
    available_stocks = [stock for stock in selected_stocks if stock in df.columns]
    if available_stocks:
        fig2 = px.line(df[available_stocks], x=df.index, y=df[available_stocks].columns, title="Historical Trends")
        graphs.append(dcc.Graph(figure=fig2))
    
    return graphs

if __name__ == "__main__":
    server = app.server  # Ensure server is properly assigned
    port = int(os.environ.get("PORT", 8080))
    app.run_server(host="0.0.0.0", port=port)

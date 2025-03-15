import subprocess
import os

# Step 1: Install required packages before importing
subprocess.run(['pip', 'install', 'yfinance', 'dash', 'plotly', 'pmdarima', 'gunicorn'])

import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import pmdarima as pm

# Step 2: Create Dash App for Render Deployment
app = Dash(__name__)
server = app.server  # Required for gunicorn on Render

default_stocks = ["RELIANCE.NS", "TCS.NS"]  # Default stocks to show initially

app.layout = html.Div([
    html.H1("Stock Investment Analysis"),
    html.Label("Select Stocks to Analyze:"),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[],  # Will be updated after data fetch
        multi=True,
        value=default_stocks
    ),
    html.Label("Rearrange Graphs:"),
    dcc.Dropdown(
        id='graph-layout',
        options=[
            {'label': "Risk-Return", 'value': "Risk-Return"},
            {'label': "ROI Bar", 'value': "ROI Bar"},
            {'label': "Historical Trends", 'value': "Historical Trends"},
            {'label': "Investment Simulation", 'value': "Investment Simulation"}
        ],
        multi=True,
        value=["Risk-Return", "ROI Bar", "Historical Trends", "Investment Simulation"]
    ),
    html.Div(id='graph-container')
])

# Step 3: Fetch Stock Data Only When the App Runs
def fetch_data():
    global df, returns_df, performance_df
    nifty50_stocks = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS", "LT.NS",
        "SBIN.NS", "ASIANPAINT.NS", "AXISBANK.NS", "DMART.NS", "MARUTI.NS", "ULTRACEMCO.NS", "TITAN.NS",
        "SUNPHARMA.NS", "M&M.NS", "NESTLEIND.NS", "WIPRO.NS", "ADANIGREEN.NS", "TATASTEEL.NS", "JSWSTEEL.NS",
        "POWERGRID.NS", "ONGC.NS", "NTPC.NS", "COALINDIA.NS", "BPCL.NS", "IOC.NS", "TECHM.NS", "INDUSINDBK.NS"
    ]
    df = yf.download(nifty50_stocks, start="2020-01-01", end="2024-12-31")["Close"].dropna()
    returns_df = df.pct_change().dropna()
    roi = returns_df.mean() * 252
    volatility = returns_df.std() * np.sqrt(252)
    performance_df = pd.DataFrame({'Stock': roi.index, 'ROI': roi.values, 'Volatility': volatility.values})
fetch_data()

@app.callback(
    Output('stock-dropdown', 'options'),
    Input('stock-dropdown', 'value')
)
def update_dropdown(value):
    return [{'label': stock, 'value': stock} for stock in performance_df['Stock']]

# Step 4: Callbacks to update graphs dynamically
@app.callback(
    Output('graph-container', 'children'),
    Input('graph-layout', 'value'),
    Input('stock-dropdown', 'value')
)
def update_graphs(selected_graphs, selected_stocks):
    if not selected_stocks:
        selected_stocks = default_stocks  # Ensure there are selected stocks
    graphs = []
    
    if "Risk-Return" in selected_graphs and not performance_df.empty:
        fig = px.scatter(performance_df, x='Volatility', y='ROI', text='Stock', title="Risk vs Return")
        graphs.append(dcc.Graph(figure=fig))
    
    if "ROI Bar" in selected_graphs:
        bucket_df = performance_df[performance_df['Stock'].isin(selected_stocks)]
        if not bucket_df.empty:
            fig = px.bar(bucket_df, x='Stock', y='ROI', title="Selected Stocks ROI", color='Stock')
            graphs.append(dcc.Graph(figure=fig))
    
    if "Historical Trends" in selected_graphs:
        available_stocks = [stock for stock in selected_stocks if stock in df.columns]
        if available_stocks:
            trend_df = df[available_stocks]
            fig = px.line(trend_df, x=trend_df.index, y=trend_df.columns, title="Historical Trends")
            graphs.append(dcc.Graph(figure=fig))
    
    if "Investment Simulation" in selected_graphs:
        sim_results = {}
        initial_investment = 10000
        for stock in selected_stocks:
            if stock in returns_df.columns:
                sim_results[stock] = (initial_investment * (1 + returns_df[stock]).cumprod())
        if sim_results:
            sim_df = pd.DataFrame(sim_results)
            fig = px.line(sim_df, x=sim_df.index, y=sim_df.columns, title="Investment Simulation")
            graphs.append(dcc.Graph(figure=fig))
    
    return graphs if graphs else [html.P("No data available for selected stocks.")]  # Show message if no graphs

# Step 5: Run the Dash App on Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    app.run_server(host='0.0.0.0', port=port, debug=True)

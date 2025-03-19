import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
import os
from constants import CPU_UTIL_CSV, FORECAST_DIR

# File path to your CSV
file_path = CPU_UTIL_CSV
# Load the dataset
df = pd.read_csv(file_path)

# Ensure the timestamp column is a datetime object
df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d-%m-%Y %H:%M")

# If needed, rename columns to suit Prophet's requirements: "ds" for datetime and "y" for value
# We will do this on a per-server basis.
forecast_results = {}  # Dictionary to store forecast data for each server

# Define a future forecast period (e.g., next 7 days) 
forecast_period_hours = 365 * 24  # forecast horizon in hours
# Convert to 5-min intervals: each hour has 12 intervals.
periods = forecast_period_hours * 12

# Loop over each server
for server, group in df.groupby('server_name'):
    print(f"Processing forecast for {server}")
    # Prepare the data for Prophet
    server_df = group[['timestamp', 'cpu_utilization']].rename(columns={'timestamp': 'ds', 'cpu_utilization': 'y'})
    server_df = server_df.sort_values('ds')
    
    # Initialize and fit the Prophet model
    m = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True
    )
    # Optional: add custom seasonalities if you need finer control
    m.add_seasonality(name='weekly', period=7, fourier_order=3)
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    
    m.fit(server_df)
    
    # Create a DataFrame to hold predictions
    future = m.make_future_dataframe(periods=periods, freq='5T')
    forecast = m.predict(future)
    
    # Save forecast results in the dictionary
    forecast_results[server] = forecast
    
    # Plot forecast
    fig = m.plot(forecast)
    # plt.title(f'CPU Utilization Forecast for {server}')
    # plt.xlabel('Date')
    # plt.ylabel('CPU Utilization (%)')
    # plt.show()
    m.plot_components(forecast).savefig(os.path.join(FORECAST_DIR,f'{server}.png'))

# Optionally, combine forecast results into a single CSV per server.
output_dir = FORECAST_DIR
os.makedirs(output_dir, exist_ok=True)

for server, forecast in forecast_results.items():
    output_file = os.path.join(output_dir, f"{server}_forecast.csv")
    forecast.to_csv(output_file, index=False)
    print(f"Saved forecast for {server} to {output_file}")

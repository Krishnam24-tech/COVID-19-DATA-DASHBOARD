import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="Global COVID-19 Data Dashboard",
    layout="wide"
)
st.title("Global COVID-19 Data Dashboard")
st.markdown("This dashboard analyzes and visualizes COVID-19 data from the Johns Hopkins University CSSE dataset.")

## Data loading and caching
## Use streamlit caching to avoid reloading data on every interaction
@st.cache_data
def load_data():
    base_url="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
    # Load the datasets
    confirmed_df = pd.read_csv(base_url + "time_series_covid19_confirmed_global.csv")
    deaths_df = pd.read_csv(base_url + "time_series_covid19_deaths_global.csv")
    recovered_df = pd.read_csv(base_url + "time_series_covid19_recovered_global.csv")

    # --- Data Preprocessing ---
    # Melt the dataframes to a long format
    dates = confirmed_df.columns[4:]
    confirmed_melted = confirmed_df.melt(
        id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
        value_vars=dates,
        var_name='Date',
        value_name='Confirmed'
    )
    deaths_melted = deaths_df.melt(
        id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
        value_vars=dates,
        var_name='Date',
        value_name='Deaths'
    )
    recovered_melted = recovered_df.melt(
        id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
        value_vars=dates,
        var_name='Date',
        value_name='Recovered'
    )
    # Convert 'Date' column to datetime objects
    confirmed_melted['Date'] = pd.to_datetime(confirmed_melted['Date'])
    deaths_melted['Date'] = pd.to_datetime(deaths_melted['Date'])
    recovered_melted['Date'] = pd.to_datetime(recovered_melted['Date'])
    
    # Merge the dataframes
    full_data = pd.merge(
        left=confirmed_melted,
        right=deaths_melted,
        on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long'],
        how='left'
    )
    full_data = pd.merge(
        left=full_data,
        right=recovered_melted,
        on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long'],
        how='left'
    )
    # Handle missing values (fill with 0)
    full_data[['Confirmed', 'Deaths', 'Recovered']] = full_data[['Confirmed', 'Deaths', 'Recovered']].fillna(0)
    
    # Aggregate data by country and date
    country_data = full_data.groupby(['Country/Region', 'Date']).sum().reset_index()

    # Calculate active cases and new daily cases
    country_data['Active'] = country_data['Confirmed'] - country_data['Deaths'] - country_data['Recovered']
    country_data['New Cases'] = country_data.groupby('Country/Region')['Confirmed'].diff().fillna(0)
    
    return country_data

# Load the data
data = load_data()

# --- Sidebar for User Input ---
st.sidebar.header("User Options")
country_list = data['Country/Region'].unique()
selected_country = st.sidebar.selectbox("Select a Country", country_list, index=list(country_list).index("India"))

# Filter data based on selected country
country_df = data[data['Country/Region'] == selected_country]

# --- Main Page Display ---

# Display Key Metrics
st.header(f"📊 Key Metrics for {selected_country}")
latest_data = country_df[country_df['Date'] == country_df['Date'].max()]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Confirmed", f"{latest_data['Confirmed'].iloc[0]:,}")
col2.metric("Total Deaths", f"{latest_data['Deaths'].iloc[0]:,}")
col3.metric("Total Recovered", f"{latest_data['Recovered'].iloc[0]:,}")
col4.metric("Total Active", f"{latest_data['Active'].iloc[0]:,}")

# --- Visualizations ---
st.header(f"📈 Charts for {selected_country}")

# 1. Time Series Plot for Cumulative Cases using Matplotlib and Seaborn
# The ax=ax1 argument tells Seaborn to draw this specific line plot on the pre-existing set of axes named ax1 that you created with Matplotlib.
fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.lineplot(data=country_df, x='Date', y='Confirmed', ax=ax1, label='Confirmed', color='blue')
sns.lineplot(data=country_df, x='Date', y='Deaths', ax=ax1, label='Deaths', color='red')
sns.lineplot(data=country_df, x='Date', y='Recovered', ax=ax1, label='Recovered', color='green')
ax1.set_title(f'Cumulative COVID-19 Cases Over Time in {selected_country}')
ax1.set_xlabel('Date')
ax1.set_ylabel('Number of Cases')
ax1.legend()
ax1.grid(True)
st.pyplot(fig1)

# 2. Bar Chart for Daily New Cases
fig2, ax2 = plt.subplots(figsize=(12, 6))
# Plotting a 14-day rolling average to smooth the data
ax2.bar(country_df['Date'], country_df['New Cases'], label='Daily New Cases', color='skyblue')
rolling_avg = country_df['New Cases'].rolling(window=14).mean()
ax2.plot(country_df['Date'], rolling_avg, color='orange', label='14-Day Rolling Average', linewidth=2)
ax2.set_title(f'Daily New Cases in {selected_country}')
ax2.set_xlabel('Date')
ax2.set_ylabel('Number of New Cases')
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)

# --- Display Raw Data ---
if st.sidebar.checkbox("Show Raw Data Table"):
    st.header("Raw Data")
    st.write(country_df.sort_values('Date', ascending=False))

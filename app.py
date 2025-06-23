# app.py
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import os

# --- Page Config ---
st.set_page_config(layout="wide", page_title="PhonePe Pulse Dashboard", page_icon="📊")

# --- Custom Background and Styles ---
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #8e2de2, #4a00e0);
        color: white;
    }
    .reportview-container {
        background-color: transparent;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(to bottom, #4a00e0, #8e2de2);
        color: white;
    }
    h1, h2, h3, h4 {
        color: #ffffff;
    }
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-size: 1em;
    }
    .stButton > button:hover {
        background-color: #ff1c1c;
    }
    .css-1d391kg {  /* Title text */
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 PhonePe Pulse Dashboard (2018 - 2024)")
st.markdown("##### Visualize UPI transaction trends across India with interactive charts and maps.")

# --- Sidebar Inputs ---
years = [str(y) for y in range(2018, 2025)]
quarters = ['1', '2', '3', '4']
chart_type = st.sidebar.selectbox("🧩 Select Chart Type", ["Bar Chart", "Pie Chart", "Line Chart"])
value_type = st.sidebar.selectbox("📈 Select Value Metric", ["Transaction Amount", "Transaction Count"])
selected_year = st.sidebar.selectbox("📅 Select Year", years)
selected_quarter = st.sidebar.selectbox("📆 Select Quarter", quarters)

# --- File Path ---
json_path = f"phonepe_data/aggregated/transaction/country/india/{selected_year}/{selected_quarter}.json"

# --- Main Logic ---
if not os.path.exists(json_path):
    st.error(f"❌ Data not found for {selected_year} Q{selected_quarter}")
else:
    with open(json_path, "r") as f:
        data = json.load(f)

    records = []
    for entry in data["data"]["transactionData"]:
        for instrument in entry["paymentInstruments"]:
            records.append({
                "Transaction Type": entry["name"],
                "Instrument Type": instrument["type"],
                "Transaction Count": instrument["count"],
                "Transaction Amount": instrument["amount"]
            })

    df = pd.DataFrame(records)

    # Display data table
    st.subheader(f"📋 Transaction Summary for {selected_year} Q{selected_quarter}")
    st.dataframe(df.sort_values(by=value_type, ascending=False), use_container_width=True)

    # Chart
    st.subheader(f"📊 {chart_type} - {value_type}")
    if chart_type == "Bar Chart":
        fig = px.bar(df.sort_values(value_type, ascending=False),
                     x='Transaction Type', y=value_type, color='Transaction Type')
    elif chart_type == "Pie Chart":
        fig = px.pie(df, names='Transaction Type', values=value_type)
    elif chart_type == "Line Chart":
        fig = px.line(df.sort_values(value_type, ascending=False),
                      x='Transaction Type', y=value_type, markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Map View
    st.subheader("🗺️ India Map View - Transaction Amount by State")
    map_path = f"phonepe_data/aggregated/transaction/statewise/{selected_year}/{selected_quarter}.json"
    if os.path.exists(map_path):
        with open(map_path, "r") as f:
            map_data = json.load(f)

        state_records = []
        for state, info in map_data["data"]["states"].items():
            state_records.append({
                "State": state,
                "Transaction Count": info["transactionCount"],
                "Transaction Amount": info["transactionAmount"]
            })

        state_df = pd.DataFrame(state_records)

        india_geojson = "https://raw.githubusercontent.com/ronak-07/India-GeoJSON/main/india_states.geojson"

        fig_map = px.choropleth(
            state_df,
            geojson=india_geojson,
            featureidkey="properties.ST_NM",
            locations="State",
            color="Transaction Amount",
            color_continuous_scale="Oranges",
            title=f"State-wise Transactions ({selected_year} Q{selected_quarter})"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("⚠️ State-wise JSON not found. Please add it to 'aggregated/transaction/statewise/...'.")

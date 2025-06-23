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
            # 🗺️ India Map View - Final Fixed
    st.subheader("🗺️ India Map View - Transaction Amount by State")

    map_path = f"state_summary/{selected_year}/{selected_quarter}.json"
    india_geojson = "india_state.geojson"

    if os.path.exists(map_path):
        with open(map_path, "r") as f:
            map_data = json.load(f)

        # Create DataFrame
        state_records = []
        for state, info in map_data["data"]["states"].items():
            state_records.append({
                "State": state,
                "Transaction Count": info["transactionCount"],
                "Transaction Amount": info["transactionAmount"]
            })
        state_df = pd.DataFrame(state_records)

        # Normalize state names
        state_df["State"] = state_df["State"].str.title().str.replace("-", " ").str.strip()
        state_name_mapping = {
            "Andaman & Nicobar Islands": "Andaman and Nicobar",
            "Dadra & Nagar Haveli & Daman & Diu": "Dadra and Nagar Haveli",
            "Jammu & Kashmir": "Jammu and Kashmir",
            "Odisha": "Orissa",
            "Uttarakhand": "Uttaranchal"
}
        state_df["State"] = state_df["State"].replace(state_name_mapping)

        # Load GeoJSON and extract matching keys
        with open(india_geojson, "r") as f:
            gj = json.load(f)

        geojson_states = [feature["properties"]["NAME_1"] for feature in gj["features"]]

        mismatched = state_df[~state_df["State"].isin(geojson_states)]
        if not mismatched.empty:
            st.warning(f"⚠️ These states don't match GeoJSON and won't show: {mismatched['State'].tolist()}")

        # Plot
        fig_map = px.choropleth(
            state_df[state_df["State"].isin(geojson_states)],
            geojson=gj,
            featureidkey="properties.NAME_1",
            locations="State",
            color="Transaction Amount",
            color_continuous_scale="Oranges",
            title=f"State-wise Transactions ({selected_year} Q{selected_quarter})"
        )
        fig_map.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor='rgba(0,0,0,0)'  # removes white background
)

        fig_map.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=650  # ⬆️ increase height
)

st.plotly_chart(fig_map, use_container_width=True)

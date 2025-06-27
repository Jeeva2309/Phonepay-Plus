import json
import pandas as pd
import streamlit as st
import plotly.express as px
import os
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(layout="wide", page_title="PhonePe Pulse Dashboard", page_icon="📊")

# --- Custom Styles ---
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
        background-color: transparent;
        color: white;
        font-size: 16px;
        padding: 0.4em 1em;
        border: 2px solid white;
        border-radius: 12px;
        transition: 0.3s ease-in-out;
    }
    .stButton > button:hover {
        color: #ffcc00;
        border-color: #ffcc00;
        background-color: rgba(255, 255, 255, 0.1);
    }
    .css-1d391kg {
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("📊 PhonePe Pulse Dashboard (2018 - 2024)")
st.markdown("##### Visualize UPI transaction trends across India with interactive charts and 3D maps.")

# --- Sidebar Inputs ---
years = [str(y) for y in range(2018, 2025)]
quarters = ['1', '2', '3', '4']
chart_type = st.sidebar.selectbox("📊 Select Chart Type", ["Bar Chart", "Pie Chart", "Line Chart"], key="chart_type")
value_type = st.sidebar.selectbox("💡 Select Value Metric", ["Transaction Amount", "Transaction Count"], key="value_type")
selected_year = st.sidebar.selectbox("📅 Select Year", years, key="year")
selected_quarter = st.sidebar.selectbox("⌛ Select Quarter", quarters, key="quarter")

# --- Load all states dynamically ---
states_path = "data/data/aggregated/transaction/country/india/state"
if os.path.exists(states_path):
    state_list = sorted([
        name for name in os.listdir(states_path)
        if os.path.isdir(os.path.join(states_path, name))
    ])
else:
    st.error(f"❌ Directory not found: {states_path}")
    state_list = []

selected_state = st.sidebar.selectbox("📍 Select a State", state_list, key="state_for_sidebar")

# --- Paths ---
txn_json_path = f"phonepe_data/aggregated/transaction/country/india/{selected_year}/{selected_quarter}.json"
map_json_path = f"state_summary/{selected_year}/{selected_quarter}.json"
india_geojson_path = "india_state.geojson"
json_path_user = f"data/data/aggregated/user/country/india/{selected_year}/{selected_quarter}.json"

# --- Tabs Layout ---
tab1, tab2 = st.tabs(["Transaction Data", "User Data"])

# ----------------------------
# TAB 1: TRANSACTION DATA
# ----------------------------
with tab1:
    if not os.path.exists(txn_json_path):
        st.error(f"❌ Data not found for {selected_year} Q{selected_quarter}")
    else:
        with open(txn_json_path, "r") as f:
            data = json.load(f)

        txn_records = []
        for entry in data["data"].get("transactionData", []):
            for instrument in entry.get("paymentInstruments", []):
                txn_records.append({
                    "Transaction Type": entry["name"],
                    "Instrument Type": instrument["type"],
                    "Transaction Count": instrument["count"],
                    "Transaction Amount": instrument["amount"]
                })

        df = pd.DataFrame(txn_records)

        st.subheader(f"📋 Transaction Summary for {selected_year} Q{selected_quarter}")
        st.dataframe(df.sort_values(by=value_type, ascending=False), use_container_width=True)

        st.subheader(f"📈 {chart_type} - {value_type}")
        if chart_type == "Bar Chart":
            fig = px.bar(df.sort_values(value_type, ascending=False), x='Transaction Type', y=value_type, color='Transaction Type')
        elif chart_type == "Pie Chart":
            fig = px.pie(df, names='Transaction Type', values=value_type)
        elif chart_type == "Line Chart":
            fig = px.line(df.sort_values(value_type, ascending=False), x='Transaction Type', y=value_type, markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # --- Map View ---
        st.subheader("🗽 India Map View - State-wise " + value_type)
        if os.path.exists(map_json_path):
            with open(map_json_path, "r") as f:
                map_data = json.load(f)

            with open(india_geojson_path, "r") as f:
                gj = json.load(f)

            state_records = []
            for state, info in map_data["data"]["states"].items():
                state_records.append({
                    "State": state,
                    "Transaction Count": info["transactionCount"],
                    "Transaction Amount": info["transactionAmount"]
                })

            state_df = pd.DataFrame(state_records)
            state_df["State"] = state_df["State"].str.title().str.replace("-", " ").str.strip()
            state_name_mapping = {
                "Andaman & Nicobar Islands": "Andaman and Nicobar",
                "Dadra & Nagar Haveli & Daman & Diu": "Dadra and Nagar Haveli",
                "Jammu & Kashmir": "Jammu and Kashmir",
                "Odisha": "Orissa",
                "Uttarakhand": "Uttaranchal"
            }
            state_df["State"] = state_df["State"].replace(state_name_mapping)

            geojson_states = [feature["properties"]["NAME_1"] for feature in gj["features"]]
            mismatched = state_df[~state_df["State"].isin(geojson_states)]
            if not mismatched.empty:
                st.warning(f"⚠️ States not in GeoJSON: {mismatched['State'].tolist()}")

            fig_map = px.choropleth_mapbox(
                state_df,
                geojson=gj,
                locations="State",
                featureidkey="properties.NAME_1",
                color=state_df[value_type],
                hover_name="State",
                hover_data=["Transaction Amount", "Transaction Count"],
                color_continuous_scale="Oranges",
                mapbox_style="carto-darkmatter",
                center={"lat": 22.5937, "lon": 78.9629},
                zoom=4,
                opacity=0.85,
                height=650
            )
            fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_map, use_container_width=True)

# ----------------------------
# TAB 2: USER DATA
# ----------------------------
with tab2:
    if not os.path.exists(json_path_user):
        st.error(f"❌ User data not found for {selected_year} Q{selected_quarter}")
    else:
        with open(json_path_user, "r") as f:
            user_data = json.load(f)

        total_users = user_data["data"].get("registeredUsers", 0)
        app_opens = user_data["data"].get("appOpens", 0)
        by_device = user_data["data"].get("usersByDevice", [])

        st.subheader(f"👥 User Summary for {selected_year} Q{selected_quarter}")
        st.metric("Registered Users", f"{total_users:,}")
        st.metric("App Opens", f"{app_opens:,}")

        if by_device:
            df_device = pd.DataFrame(by_device)
            st.subheader("📱 Users by Device Brand")
            fig_pie = px.pie(df_device, names="brand", values="count", title="User Device Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
            st.dataframe(df_device, use_container_width=True)
        else:
            st.info("ℹ No device data available.")

# ==================== 📉 INSIGHTS SECTION ====================
st.markdown("## ✨ Fun Facts Carousel")
if st.button("✨ Show Fun Insights"):
    carousel_html = """<html><head><style>
    .slider-container { overflow: hidden; width: 100%; }
    .slider { display: flex; gap: 20px; animation: slide 40s linear infinite; }
    .card { min-width: 300px; background: #4a148c; border-radius: 15px; color: white; padding: 20px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.3); }
    .card:nth-child(2) { background: #00695c; }
    .card:nth-child(3) { background: #3e2723; }
    .card:nth-child(4) { background: #1a237e; }
    .card:nth-child(5) { background: #880e4f; }
    @keyframes slide {
        0% { transform: translateX(0); }
        20% { transform: translateX(-320px); }
        40% { transform: translateX(-640px); }
        60% { transform: translateX(-960px); }
        80% { transform: translateX(-1280px); }
        100% { transform: translateX(0); }
    }
    </style></head><body>
    <div class='slider-container'><div class='slider'>
    <div class='card'><h3>The digital red note</h3><h1>₹1000</h1><p>Most common amount transferred to a contact</p></div>
    <div class='card'><h3>Shagun for good luck!</h3><h1>Over 30%</h1><p>Users transferred ₹500 as a gift</p></div>
    <div class='card'><h3>Post work-hour transfers</h3><h1>10%</h1><p>Transactions between 8–10 PM</p></div>
    <div class='card'><h3>Small towns, big saves!</h3><h1>₹30,000</h1><p>Average digital savings in Tier-3 towns</p></div>
    <div class='card'><h3>Scaling fast!</h3><h1>61% ↑</h1><p>Year-on-year growth in merchant QR usage</p></div>
    </div></div></body></html>"""
    components.html(carousel_html, height=280)

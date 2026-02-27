"""
AquaForge Land Screener — Interactive Freshwater-Rich Land Parcel Discovery Tool
=================================================================================
A professional-grade screener for discovering raw/vacant land parcels with high
potential for undiscovered freshwater resources, mineral deposits, and timber value
across all 50 U.S. states.

Run:  streamlit run app.py
Requires: see requirements.txt
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import json

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaForge Land Screener",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — dark terminal aesthetic
# ──────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-card: #1a2236;
        --accent-blue: #00b4d8;
        --accent-cyan: #06d6a0;
        --accent-gold: #f4a261;
        --accent-red: #ef476f;
        --text-primary: #e0e6ed;
        --text-secondary: #8899aa;
        --border-color: #1e2d44;
    }

    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0d1321 50%, #0a0e17 100%);
        color: var(--text-primary);
    }

    header[data-testid="stHeader"] {
        background: rgba(10, 14, 23, 0.95) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1525 0%, #111827 100%) !important;
        border-right: 1px solid var(--border-color);
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown label,
    section[data-testid="stSidebar"] label {
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
    }

    h1, h2, h3 {
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: -0.02em;
    }

    .metric-card {
        background: linear-gradient(135deg, var(--bg-card), #1e293b);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: var(--accent-blue);
    }
    .metric-card .value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.65rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.25rem 0;
    }
    .metric-card .label {
        font-family: 'Inter', sans-serif;
        color: var(--text-secondary);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .hero-banner {
        background: linear-gradient(135deg, rgba(0,180,216,0.12), rgba(6,214,160,0.08));
        border: 1px solid rgba(0,180,216,0.25);
        border-radius: 14px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.2rem;
    }
    .hero-banner h1 {
        font-size: 1.9rem;
        background: linear-gradient(90deg, #00b4d8, #06d6a0, #f4a261);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero-banner p {
        color: var(--text-secondary);
        font-size: 0.92rem;
        margin: 0;
    }

    .score-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-secondary);
        border-radius: 10px;
        padding: 4px;
        border: 1px solid var(--border-color);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--text-secondary);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        padding: 0.45rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,180,216,0.2), rgba(6,214,160,0.15)) !important;
        color: var(--accent-cyan) !important;
        border: 1px solid rgba(0,180,216,0.3);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border-color);
        border-radius: 10px;
        overflow: hidden;
    }

    .disclaimer {
        background: rgba(239,71,111,0.08);
        border: 1px solid rgba(239,71,111,0.2);
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-top: 2rem;
    }

    .stSlider > div > div { color: var(--text-secondary); }

    div.stButton > button {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        border-radius: 8px;
        transition: all 0.2s;
    }
    </style>
    """, unsafe_allow_html=True)


inject_css()


# ──────────────────────────────────────────────────────────────────────────────
# DATA GENERATION — 800 realistic synthetic parcels across all 50 states
# ──────────────────────────────────────────────────────────────────────────────
# PRODUCTION NOTE: Replace this function with real API calls:
#   • Parcel listings → Regrid API (regrid.com), ATTOM Data Solutions, or LandWatch
#   • Water data      → USGS Water Data APIs (waterservices.usgs.gov), National Aquifer codes
#   • Minerals        → USGS MRDS / USMIN (mrdata.usgs.gov) WMS/WFS
#   • Timber          → USDA Forest Service FIA DataMart / FSGeodata Clearinghouse

# State centroids + metadata for realistic clustering
STATE_DATA = {
    "AL": (32.8, -86.8, "Alabama"),    "AK": (64.0, -153.0, "Alaska"),
    "AZ": (34.2, -111.7, "Arizona"),   "AR": (34.8, -92.2, "Arkansas"),
    "CA": (37.2, -119.5, "California"),"CO": (39.0, -105.5, "Colorado"),
    "CT": (41.6, -72.7, "Connecticut"),"DE": (39.0, -75.5, "Delaware"),
    "FL": (28.6, -82.4, "Florida"),    "GA": (32.7, -83.5, "Georgia"),
    "HI": (20.5, -157.5, "Hawaii"),    "ID": (44.4, -114.6, "Idaho"),
    "IL": (40.0, -89.4, "Illinois"),   "IN": (39.9, -86.3, "Indiana"),
    "IA": (42.0, -93.5, "Iowa"),       "KS": (38.5, -98.3, "Kansas"),
    "KY": (37.8, -85.7, "Kentucky"),   "LA": (30.9, -92.0, "Louisiana"),
    "ME": (45.3, -69.2, "Maine"),      "MD": (39.0, -76.8, "Maryland"),
    "MA": (42.2, -71.8, "Massachusetts"),"MI": (44.3, -85.4, "Michigan"),
    "MN": (46.3, -94.3, "Minnesota"), "MS": (32.7, -89.7, "Mississippi"),
    "MO": (38.4, -92.5, "Missouri"),   "MT": (47.0, -109.6, "Montana"),
    "NE": (41.5, -99.8, "Nebraska"),   "NV": (39.3, -116.6, "Nevada"),
    "NH": (43.7, -71.6, "New Hampshire"),"NJ": (40.1, -74.7, "New Jersey"),
    "NM": (34.5, -106.0, "New Mexico"),"NY": (42.9, -75.5, "New York"),
    "NC": (35.5, -79.8, "North Carolina"),"ND": (47.5, -100.5, "North Dakota"),
    "OH": (40.4, -82.7, "Ohio"),       "OK": (35.5, -97.5, "Oklahoma"),
    "OR": (44.0, -120.5, "Oregon"),    "PA": (41.0, -77.5, "Pennsylvania"),
    "RI": (41.7, -71.5, "Rhode Island"),"SC": (34.0, -81.0, "South Carolina"),
    "SD": (44.4, -100.2, "South Dakota"),"TN": (35.9, -86.4, "Tennessee"),
    "TX": (31.5, -99.3, "Texas"),      "UT": (39.3, -111.7, "Utah"),
    "VT": (44.1, -72.6, "Vermont"),    "VA": (37.5, -78.8, "Virginia"),
    "WA": (47.4, -120.5, "Washington"),"WV": (38.6, -80.6, "West Virginia"),
    "WI": (44.6, -89.8, "Wisconsin"),  "WY": (43.0, -107.5, "Wyoming"),
}

# States with higher parcel density (Western resource-rich states)
HIGH_DENSITY_STATES = ["CA","NV","AZ","NM","TX","CO","MT","ID","OR","WA","UT","WY","AK"]
GOLD_STATES = ["NV","CA","AK","CO","AZ","MT","ID","OR","UT","NM","SD","GA","NC","WY"]
AQUIFER_STATES = ["NE","KS","TX","OK","SD","ND","IA","MN","CO","NM","WY","MT","AR","FL","ID"]
TIMBER_STATES = ["OR","WA","ME","WI","MN","MI","GA","AL","MS","NC","VA","WV","ID","MT","CA","AR"]

COUNTIES_BY_STATE = {
    "CA": ["Kern","Inyo","Lassen","Modoc","Siskiyou","Shasta","Trinity","Humboldt","Plumas","Sierra","El Dorado","Calaveras"],
    "NV": ["Elko","Humboldt","Pershing","Lander","Eureka","White Pine","Nye","Mineral","Esmeralda","Churchill"],
    "AZ": ["Mohave","Coconino","Yavapai","Gila","Graham","Greenlee","Santa Cruz","Cochise","Pinal","La Paz"],
    "TX": ["Brewster","Presidio","Jeff Davis","Culberson","Hudspeth","Terrell","Val Verde","Pecos","Reeves","Crockett","Edwards","Real","Uvalde","Llano"],
    "CO": ["Park","Teller","Clear Creek","Gilpin","Lake","Chaffee","Fremont","Custer","Huerfano","Las Animas","Mineral","San Juan"],
    "MT": ["Lewis and Clark","Jefferson","Broadwater","Meagher","Deer Lodge","Silver Bow","Madison","Beaverhead","Granite","Powell"],
    "ID": ["Idaho","Lemhi","Custer","Boise","Valley","Clearwater","Shoshone","Bonner","Boundary","Benewah"],
    "OR": ["Josephine","Jackson","Douglas","Lane","Linn","Marion","Grant","Baker","Malheur","Harney"],
    "WA": ["Okanogan","Ferry","Stevens","Pend Oreille","Chelan","Kittitas","Klickitat","Skamania","Lewis","Grays Harbor"],
    "NE": ["Cherry","Custer","Blaine","Thomas","Hooker","Grant","Arthur","McPherson","Keith","Lincoln"],
    "KS": ["Finney","Ford","Gray","Haskell","Meade","Clark","Comanche","Barber","Harper","Kiowa"],
    "FL": ["Levy","Gilchrist","Alachua","Marion","Citrus","Hernando","Pasco","Polk","Highlands","DeSoto"],
    "AK": ["Fairbanks North Star","Southeast Fairbanks","Yukon-Koyukuk","Denali","Matanuska-Susitna","Kenai Peninsula","Valdez-Cordova","Nome","Bethel","Kodiak Island"],
}

MINERALS_ALL = ["Gold","Silver","Copper","Lithium","Rare Earth Elements","Oil/Gas","Uranium","Coal"]
FOREST_TYPES = ["Hardwood","Softwood","Mixed","None"]
ZONING_TYPES = ["Agricultural","Residential","Mining-friendly","Recreational","Unzoned","Conservation","Mixed-Use"]
WATER_RIGHTS = ["Adjudicated","Riparian","Prior Appropriation","None","Unknown"]
SELLER_TYPES = ["Private","Bank-owned","Government Surplus","Estate","Corporate"]
SOIL_CLASSES = ["Class I","Class II","Class III","Class IV","Class V","Class VI","Class VII","Class VIII"]

def _county_for_state(rng, state_abbr):
    if state_abbr in COUNTIES_BY_STATE:
        return rng.choice(COUNTIES_BY_STATE[state_abbr])
    return f"{STATE_DATA[state_abbr][2]} County"

@st.cache_data(show_spinner=False)
def generate_parcels(n=800, seed=42):
    """Generate realistic synthetic parcel dataset distributed across all 50 states."""
    rng = np.random.RandomState(seed)
    records = []

    # Distribute parcels: more in resource-rich Western states
    states = list(STATE_DATA.keys())
    weights = np.array([3.0 if s in HIGH_DENSITY_STATES else 1.0 for s in states])
    weights /= weights.sum()
    assigned_states = rng.choice(states, size=n, p=weights)

    for i, st_abbr in enumerate(assigned_states):
        lat_c, lon_c, state_name = STATE_DATA[st_abbr]

        # Scatter around centroid (tighter for small states)
        spread = 2.5 if st_abbr not in ["CT","DE","RI","NJ","MA","NH","VT","MD","HI"] else 0.5
        if st_abbr == "AK":
            spread = 5.0
        lat = lat_c + rng.normal(0, spread * 0.4)
        lon = lon_c + rng.normal(0, spread * 0.6)

        county = _county_for_state(rng, st_abbr)

        # --- Acreage (log-normal: mostly 5-500, some large ranches) ---
        acres = np.clip(rng.lognormal(4.5, 1.4), 1, 15000)
        acres = round(acres, 1)

        # --- Price logic (varies by state, size, and features) ---
        base_ppa = rng.lognormal(7.0, 0.8)  # $/acre base
        if st_abbr in ["CT","NJ","MA","MD","DE","RI","NH"]:
            base_ppa *= rng.uniform(3, 8)
        elif st_abbr in ["NV","NM","WY","MT","SD","ND","NE"]:
            base_ppa *= rng.uniform(0.1, 0.5)
        elif st_abbr == "AK":
            base_ppa *= rng.uniform(0.05, 0.3)
        base_ppa = np.clip(base_ppa, 100, 50000)
        price_per_acre = round(base_ppa, 0)
        total_price = round(acres * price_per_acre, 0)

        # --- Water Score (1-10): higher near known aquifer regions ---
        water_base = rng.uniform(1, 6)
        if st_abbr in AQUIFER_STATES:
            water_base += rng.uniform(2, 4)
        water_score = np.clip(round(water_base + rng.normal(0, 0.8), 1), 1.0, 10.0)

        aquifer_prox = round(rng.exponential(15) + 0.5, 1) if water_score < 7 else round(rng.uniform(0.5, 8), 1)
        annual_recharge = round(water_score * rng.uniform(5, 40) * (acres / 100), 1)

        # --- Gold & Mineral Potential ---
        if st_abbr in GOLD_STATES:
            gold_pot = rng.choice(["High","Medium","Low"], p=[0.2, 0.4, 0.4])
        else:
            gold_pot = rng.choice(["High","Medium","Low"], p=[0.02, 0.13, 0.85])

        num_minerals = rng.poisson(1.5)
        if st_abbr in GOLD_STATES:
            num_minerals += 1
        num_minerals = min(num_minerals, len(MINERALS_ALL))
        minerals = list(rng.choice(MINERALS_ALL, size=max(num_minerals, 0), replace=False))
        if gold_pot == "High" and "Gold" not in minerals:
            minerals.append("Gold")

        mineral_score = np.clip(round(
            ({"High": 3, "Medium": 1.5, "Low": 0.5}[gold_pot]) + len(minerals) * 0.8 + rng.normal(0, 1),
            1), 1.0, 10.0)

        # --- Timber ---
        if st_abbr in TIMBER_STATES:
            timber_score = np.clip(round(rng.uniform(4, 10) + rng.normal(0, 1), 1), 1.0, 10.0)
            forest_type = rng.choice(["Hardwood","Softwood","Mixed"], p=[0.3, 0.4, 0.3])
        else:
            timber_score = np.clip(round(rng.uniform(1, 5) + rng.normal(0, 0.5), 1), 1.0, 10.0)
            forest_type = rng.choice(FOREST_TYPES, p=[0.15, 0.1, 0.15, 0.6])

        board_feet = round(timber_score * acres * rng.uniform(30, 200), 0) if forest_type != "None" else 0
        timber_value = round(board_feet * rng.uniform(0.15, 0.60), 0)

        # --- Other attributes ---
        elevation = round(rng.uniform(50, 9000) if st_abbr not in ["FL","LA","DE"] else rng.uniform(0, 300), 0)
        soil_class = rng.choice(SOIL_CLASSES, p=[0.05,0.1,0.15,0.2,0.15,0.15,0.1,0.1])
        water_rights = rng.choice(WATER_RIGHTS, p=[0.15,0.2,0.15,0.3,0.2])
        zoning = rng.choice(ZONING_TYPES)
        dist_road = round(rng.exponential(3) + 0.1, 1)
        dist_power = round(rng.exponential(5) + 0.2, 1)
        dist_river = round(rng.exponential(8) + 0.3, 1)
        seller = rng.choice(SELLER_TYPES, p=[0.45,0.15,0.1,0.15,0.15])
        owner_name = rng.choice(["J. Smith","R. Johnson","M. Williams","T. Brown","S. Davis",
                                  "L. Martinez","K. Anderson","D. Thomas","C. Wilson","A. Garcia",
                                  "BLM Surplus","County Trust","First National","Estate of H. Lee",
                                  "Pine Creek LLC","Mesa Holdings","Range Corp","Timber Ridge Inc"])

        composite = round((water_score * 0.4 + mineral_score * 0.3 + timber_score * 0.3), 2)

        records.append({
            "id": f"AF-{i+1:04d}",
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "state": st_abbr,
            "state_name": state_name,
            "county": county,
            "acres": acres,
            "total_price": total_price,
            "price_per_acre": price_per_acre,
            "water_score": water_score,
            "aquifer_proximity_mi": aquifer_prox,
            "annual_recharge_af": annual_recharge,
            "gold_potential": gold_pot,
            "minerals": minerals,
            "mineral_score": mineral_score,
            "timber_score": timber_score,
            "forest_type": forest_type,
            "timber_board_feet": board_feet,
            "timber_value_est": timber_value,
            "elevation_ft": elevation,
            "soil_class": soil_class,
            "water_rights": water_rights,
            "zoning": zoning,
            "dist_road_mi": dist_road,
            "dist_power_mi": dist_power,
            "dist_river_mi": dist_river,
            "seller_type": seller,
            "owner": owner_name,
            "composite_score": composite,
        })

    df = pd.DataFrame(records)
    df["minerals_str"] = df["minerals"].apply(lambda x: ", ".join(x) if x else "None")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def water_color(score):
    """Return a hex color on a blue gradient for the water score."""
    if score >= 8.5: return "#003f88"
    if score >= 7:   return "#0066cc"
    if score >= 5.5: return "#0099ff"
    if score >= 4:   return "#33bbff"
    if score >= 2.5: return "#80d4ff"
    return "#b3e6ff"

def composite_color(score):
    if score >= 8:  return "#00cc44"
    if score >= 6:  return "#00b4d8"
    if score >= 4:  return "#f4a261"
    return "#8899aa"

def fmt_price(val):
    if val >= 1_000_000: return f"${val/1_000_000:.2f}M"
    if val >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:,.0f}"

def make_popup_html(row):
    gold_badge_color = {"High":"#f4a261","Medium":"#aaa","Low":"#556"}[row['gold_potential']]
    return f"""
    <div style="font-family:'Inter',sans-serif;width:320px;background:#111827;color:#e0e6ed;border-radius:10px;padding:14px;border:1px solid #1e2d44;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-family:'JetBrains Mono',monospace;font-weight:700;font-size:1rem;color:#00b4d8;">{row['id']}</span>
            <span style="background:rgba(0,180,216,0.15);color:#00b4d8;padding:2px 8px;border-radius:5px;font-size:0.75rem;">
                Score {row['composite_score']:.1f}
            </span>
        </div>
        <div style="font-size:0.82rem;color:#8899aa;margin-bottom:6px;">
            📍 {row['county']}, {row['state_name']}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:10px 0;">
            <div style="background:#1a2236;border-radius:6px;padding:6px 8px;text-align:center;">
                <div style="font-size:0.68rem;color:#8899aa;">ACRES</div>
                <div style="font-weight:600;">{row['acres']:,.1f}</div>
            </div>
            <div style="background:#1a2236;border-radius:6px;padding:6px 8px;text-align:center;">
                <div style="font-size:0.68rem;color:#8899aa;">PRICE</div>
                <div style="font-weight:600;">{fmt_price(row['total_price'])}</div>
            </div>
            <div style="background:#1a2236;border-radius:6px;padding:6px 8px;text-align:center;">
                <div style="font-size:0.68rem;color:#8899aa;">$/ACRE</div>
                <div style="font-weight:600;">{fmt_price(row['price_per_acre'])}</div>
            </div>
            <div style="background:#1a2236;border-radius:6px;padding:6px 8px;text-align:center;">
                <div style="font-size:0.68rem;color:#8899aa;">💧 WATER</div>
                <div style="font-weight:600;color:{water_color(row['water_score'])};">{row['water_score']:.1f}/10</div>
            </div>
        </div>
        <div style="font-size:0.78rem;margin:6px 0;">
            <b>Gold:</b> <span style="color:{gold_badge_color};">{row['gold_potential']}</span> &nbsp;|&nbsp;
            <b>Mineral:</b> {row['mineral_score']:.1f} &nbsp;|&nbsp;
            <b>Timber:</b> {row['timber_score']:.1f}
        </div>
        <div style="font-size:0.72rem;color:#8899aa;margin:4px 0;">
            Minerals: {row['minerals_str']}<br>
            Elevation: {row['elevation_ft']:,.0f} ft &nbsp;|&nbsp; Aquifer: {row['aquifer_proximity_mi']:.1f} mi<br>
            Water Rights: {row['water_rights']} &nbsp;|&nbsp; Zoning: {row['zoning']}
        </div>
        <a href="#" style="display:block;text-align:center;margin-top:10px;padding:6px;background:linear-gradient(90deg,#00b4d8,#06d6a0);
           color:#000;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.8rem;">
            View Listing →
        </a>
    </div>
    """

def render_metric_card(label, value, icon=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{icon} {label}</div>
        <div class="value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Parcels')
    return output.getvalue()


# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
df_all = generate_parcels(n=800, seed=42)


# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────
if "show_hot_list" not in st.session_state:
    st.session_state.show_hot_list = False
if "selected_parcel" not in st.session_state:
    st.session_state.selected_parcel = None


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 1rem;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;
              background:linear-gradient(90deg,#00b4d8,#06d6a0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              💧 AquaForge
        </span>
        <div style="font-size:0.7rem;color:#8899aa;letter-spacing:0.1em;">LAND SCREENER v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ----- Search -----
    search_query = st.text_input("🔍 Search (ID, Owner, Keyword)", "", key="search")

    # ----- Geography -----
    st.markdown("#### 🌎 Geography")
    all_states_list = sorted(df_all["state"].unique())
    selected_states = st.multiselect("States", ["All States"] + all_states_list, default=["All States"], key="states")
    if "All States" in selected_states or not selected_states:
        selected_states = all_states_list
    county_search = st.text_input("County (contains)", "", key="county")

    # ----- Price & Size -----
    st.markdown("#### 💰 Price & Size")
    price_range = st.slider("Total Price ($)", 0, 50_000_000, (0, 50_000_000), step=50_000, format="$%d", key="price")
    acres_range = st.slider("Acres", 1, 15_000, (1, 15_000), step=10, key="acres")
    ppa_range = st.slider("$/Acre", 100, 50_000, (100, 50_000), step=100, format="$%d", key="ppa")

    # ----- Freshwater -----
    st.markdown("#### 💧 Freshwater Potential")
    water_range = st.slider("Water Potential Score", 1.0, 10.0, (1.0, 10.0), step=0.5, key="water")
    aquifer_max = st.selectbox("Aquifer Proximity", ["Any","< 5 mi","< 10 mi","< 20 mi","< 50 mi"], key="aquifer")
    recharge_min = st.number_input("Min Annual Recharge (acre-ft)", min_value=0.0, value=0.0, step=10.0, key="recharge")

    # ----- Minerals -----
    st.markdown("#### ⛏️ Minerals & Resources")
    gold_filter = st.selectbox("Gold Vein Potential", ["Any","High","Medium","Low"], key="gold")
    mineral_select = st.multiselect("Must Include Minerals", MINERALS_ALL, key="minerals_filter")
    mineral_range = st.slider("Mineral Score", 1.0, 10.0, (1.0, 10.0), step=0.5, key="min_score")

    # ----- Timber -----
    st.markdown("#### 🌲 Timber & Forestry")
    timber_range = st.slider("Timber Score", 1.0, 10.0, (1.0, 10.0), step=0.5, key="timber")
    forest_filter = st.multiselect("Forest Type", FOREST_TYPES, default=[], key="forest")

    # ----- Additional -----
    with st.expander("⚙️ Additional Filters"):
        elev_range = st.slider("Elevation (ft)", 0, 10_000, (0, 10_000), step=100, key="elev")
        soil_filter = st.multiselect("Soil Class", SOIL_CLASSES, default=[], key="soil")
        wr_filter = st.multiselect("Water Rights", WATER_RIGHTS, default=[], key="wr")
        zoning_filter = st.multiselect("Zoning", ZONING_TYPES, default=[], key="zoning")
        road_max = st.number_input("Max Dist to Road (mi)", min_value=0.0, value=999.0, step=1.0, key="road")
        seller_filter = st.multiselect("Seller Type", SELLER_TYPES, default=[], key="seller")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔥 Hot List", use_container_width=True):
            st.session_state.show_hot_list = not st.session_state.show_hot_list
    with col_b:
        if st.button("↺ Reset", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k not in ["show_hot_list","selected_parcel"]:
                    del st.session_state[k]
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ──────────────────────────────────────────────────────────────────────────────
df = df_all.copy()
df = df[df["state"].isin(selected_states)]

if county_search:
    df = df[df["county"].str.contains(county_search, case=False, na=False)]

df = df[(df["total_price"] >= price_range[0]) & (df["total_price"] <= price_range[1])]
df = df[(df["acres"] >= acres_range[0]) & (df["acres"] <= acres_range[1])]
df = df[(df["price_per_acre"] >= ppa_range[0]) & (df["price_per_acre"] <= ppa_range[1])]
df = df[(df["water_score"] >= water_range[0]) & (df["water_score"] <= water_range[1])]

if aquifer_max != "Any":
    limit = float(aquifer_max.split("<")[1].strip().replace(" mi",""))
    df = df[df["aquifer_proximity_mi"] <= limit]

df = df[df["annual_recharge_af"] >= recharge_min]

if gold_filter != "Any":
    df = df[df["gold_potential"] == gold_filter]

if mineral_select:
    df = df[df["minerals"].apply(lambda m: all(x in m for x in mineral_select))]

df = df[(df["mineral_score"] >= mineral_range[0]) & (df["mineral_score"] <= mineral_range[1])]
df = df[(df["timber_score"] >= timber_range[0]) & (df["timber_score"] <= timber_range[1])]

if forest_filter:
    df = df[df["forest_type"].isin(forest_filter)]

df = df[(df["elevation_ft"] >= elev_range[0]) & (df["elevation_ft"] <= elev_range[1])]

if soil_filter:
    df = df[df["soil_class"].isin(soil_filter)]
if wr_filter:
    df = df[df["water_rights"].isin(wr_filter)]
if zoning_filter:
    df = df[df["zoning"].isin(zoning_filter)]

df = df[df["dist_road_mi"] <= road_max]

if seller_filter:
    df = df[df["seller_type"].isin(seller_filter)]

if search_query:
    q = search_query.lower()
    df = df[
        df["id"].str.lower().str.contains(q, na=False) |
        df["owner"].str.lower().str.contains(q, na=False) |
        df["county"].str.lower().str.contains(q, na=False) |
        df["minerals_str"].str.lower().str.contains(q, na=False)
    ]

if st.session_state.show_hot_list:
    df = df.nlargest(50, "composite_score")

df = df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>💧 AquaForge Land Screener</h1>
    <p>Discover freshwater-rich land parcels with hidden mineral, timber, and resource value across all 50 states.</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY METRICS
# ──────────────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    render_metric_card("Parcels", f"{len(df):,}", "📦")
with c2:
    render_metric_card("Total Acres", f"{df['acres'].sum():,.0f}", "🗺️")
with c3:
    avg_ppa = f"${df['price_per_acre'].mean():,.0f}" if len(df) else "—"
    render_metric_card("Avg $/Acre", avg_ppa, "💵")
with c4:
    hw = len(df[df['water_score'] >= 7])
    render_metric_card("High Water", str(hw), "💧")
with c5:
    hg = len(df[df['gold_potential'] == 'High'])
    render_metric_card("Gold-High", str(hg), "🥇")
with c6:
    avg_comp = f"{df['composite_score'].mean():.1f}" if len(df) else "—"
    render_metric_card("Avg Score", avg_comp, "⭐")

st.markdown("")

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab_dash, tab_map, tab_table, tab_calc, tab_about = st.tabs(
    ["📊 Dashboard", "🗺️ Map", "📋 Table", "🧮 Valuation Calc", "ℹ️ About"]
)


# ━━━━━━━━━━━━━━━━━━━━━━━━ TAB: DASHBOARD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_dash:
    if len(df) == 0:
        st.info("No parcels match your current filters. Try widening your criteria.")
    else:
        d1, d2 = st.columns(2)

        with d1:
            # Water score distribution
            fig_water = px.histogram(
                df, x="water_score", nbins=20,
                color_discrete_sequence=["#00b4d8"],
                title="Water Potential Score Distribution",
                labels={"water_score":"Water Score","count":"Parcels"},
            )
            fig_water.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899aa", family="Inter"), title_font_size=14,
                xaxis=dict(gridcolor="#1e2d44"), yaxis=dict(gridcolor="#1e2d44"),
                margin=dict(l=40,r=20,t=40,b=30), height=300,
            )
            st.plotly_chart(fig_water, use_container_width=True)

        with d2:
            # Composite scatter
            fig_scatter = px.scatter(
                df, x="price_per_acre", y="composite_score",
                size="acres", color="water_score",
                color_continuous_scale="Blues",
                hover_name="id",
                title="Value vs. Composite Score",
                labels={"price_per_acre":"$/Acre","composite_score":"Composite Score","acres":"Acres"},
            )
            fig_scatter.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899aa", family="Inter"), title_font_size=14,
                xaxis=dict(gridcolor="#1e2d44"), yaxis=dict(gridcolor="#1e2d44"),
                margin=dict(l=40,r=20,t=40,b=30), height=300,
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        d3, d4 = st.columns(2)
        with d3:
            state_counts = df.groupby("state_name").size().reset_index(name="count").sort_values("count", ascending=True).tail(15)
            fig_bar = px.bar(
                state_counts, x="count", y="state_name", orientation="h",
                color_discrete_sequence=["#06d6a0"],
                title="Top States by Parcel Count",
                labels={"count":"Parcels","state_name":"State"},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899aa", family="Inter"), title_font_size=14,
                xaxis=dict(gridcolor="#1e2d44"), yaxis=dict(gridcolor="#1e2d44"),
                margin=dict(l=10,r=20,t=40,b=30), height=350, showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with d4:
            gold_counts = df["gold_potential"].value_counts().reset_index()
            gold_counts.columns = ["Potential","Count"]
            fig_gold = px.pie(
                gold_counts, names="Potential", values="Count",
                color="Potential",
                color_discrete_map={"High":"#f4a261","Medium":"#8899aa","Low":"#334155"},
                title="Gold Potential Breakdown",
                hole=0.45,
            )
            fig_gold.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899aa", family="Inter"), title_font_size=14,
                margin=dict(l=20,r=20,t=40,b=20), height=350,
                legend=dict(font=dict(size=11)),
            )
            st.plotly_chart(fig_gold, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━ TAB: MAP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_map:
    if len(df) == 0:
        st.info("No parcels to display. Adjust your filters.")
    else:
        # Fly-to-state selector
        map_col1, map_col2, map_col3 = st.columns([2,2,3])
        with map_col1:
            fly_to = st.selectbox("Fly to State", ["Continental US"] + sorted(df["state_name"].unique().tolist()), key="fly")
        with map_col2:
            overlay = st.multiselect("Overlays", ["Aquifer Heatmap","Mineral Heatmap","Marker Clusters"], default=["Marker Clusters"], key="overlays")
        with map_col3:
            st.caption(f"Showing {min(len(df), 500)} of {len(df)} markers (capped for performance)")

        # Determine center
        if fly_to == "Continental US":
            center = [39.5, -98.5]
            zoom = 4
        else:
            row_state = df[df["state_name"] == fly_to].iloc[0] if len(df[df["state_name"] == fly_to]) > 0 else None
            if row_state is not None:
                center = [row_state["latitude"], row_state["longitude"]]
                zoom = 7
            else:
                center = [39.5, -98.5]
                zoom = 4

        m = folium.Map(
            location=center, zoom_start=zoom,
            tiles="CartoDB dark_matter",
            control_scale=True,
        )

        # Limit markers for performance
        df_map = df.head(500)

        if "Marker Clusters" in overlay:
            cluster = MarkerCluster(name="Parcels", options={"maxClusterRadius": 40})
            for _, row in df_map.iterrows():
                popup_html = make_popup_html(row)
                icon_color = "darkblue" if row["water_score"] >= 7 else "blue" if row["water_score"] >= 5 else "lightblue" if row["water_score"] >= 3 else "gray"
                folium.Marker(
                    [row["latitude"], row["longitude"]],
                    popup=folium.Popup(popup_html, max_width=340),
                    tooltip=f"{row['id']} — Water: {row['water_score']:.1f}",
                    icon=folium.Icon(color=icon_color, icon="tint", prefix="fa"),
                ).add_to(cluster)
            cluster.add_to(m)
        else:
            for _, row in df_map.iterrows():
                popup_html = make_popup_html(row)
                folium.CircleMarker(
                    [row["latitude"], row["longitude"]],
                    radius=5 + row["composite_score"] * 0.8,
                    color=water_color(row["water_score"]),
                    fill=True, fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=340),
                    tooltip=f"{row['id']} — Score: {row['composite_score']:.1f}",
                ).add_to(m)

        if "Aquifer Heatmap" in overlay and len(df_map) > 0:
            heat_data = df_map[df_map["water_score"] >= 5][["latitude","longitude","water_score"]].values.tolist()
            if heat_data:
                HeatMap(heat_data, name="Aquifer Heat", radius=25, blur=15,
                        gradient={0.4:'#0099ff', 0.7:'#0066cc', 1.0:'#003f88'}).add_to(m)

        if "Mineral Heatmap" in overlay and len(df_map) > 0:
            min_data = df_map[df_map["mineral_score"] >= 5][["latitude","longitude","mineral_score"]].values.tolist()
            if min_data:
                HeatMap(min_data, name="Mineral Heat", radius=20, blur=12,
                        gradient={0.4:'#f4a261', 0.7:'#e76f51', 1.0:'#d62828'}).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)

        st_folium(m, use_container_width=True, height=620, returned_objects=[])


# ━━━━━━━━━━━━━━━━━━━━━━━━ TAB: TABLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_table:
    if len(df) == 0:
        st.info("No parcels match your current filters.")
    else:
        st.markdown(f"**{len(df):,} parcels** matching filters")

        display_cols = [
            "id","state","county","acres","total_price","price_per_acre",
            "water_score","gold_potential","mineral_score","timber_score",
            "timber_value_est","elevation_ft","composite_score","aquifer_proximity_mi",
            "water_rights","zoning","seller_type","owner"
        ]
        df_display = df[display_cols].copy()
        df_display.columns = [
            "ID","State","County","Acres","Total Price","$/Acre",
            "Water","Gold","Mineral","Timber",
            "Timber Value $","Elevation ft","Composite","Aquifer mi",
            "Water Rights","Zoning","Seller","Owner"
        ]

        # Format currency columns
        df_display["Total Price"] = df_display["Total Price"].apply(lambda x: f"${x:,.0f}")
        df_display["$/Acre"] = df_display["$/Acre"].apply(lambda x: f"${x:,.0f}")
        df_display["Timber Value $"] = df_display["Timber Value $"].apply(lambda x: f"${x:,.0f}")

        st.dataframe(
            df_display,
            use_container_width=True,
            height=520,
            column_config={
                "Water": st.column_config.ProgressColumn("Water", min_value=1, max_value=10, format="%.1f"),
                "Mineral": st.column_config.ProgressColumn("Mineral", min_value=1, max_value=10, format="%.1f"),
                "Timber": st.column_config.ProgressColumn("Timber", min_value=1, max_value=10, format="%.1f"),
                "Composite": st.column_config.ProgressColumn("Composite", min_value=1, max_value=10, format="%.1f"),
            }
        )

        # Export
        exp_c1, exp_c2, _ = st.columns([1,1,4])
        with exp_c1:
            csv = df[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export CSV", csv, "aquaforge_parcels.csv", "text/csv", use_container_width=True)
        with exp_c2:
            xlsx = to_excel(df[display_cols])
            st.download_button("📥 Export Excel", xlsx, "aquaforge_parcels.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━ TAB: VALUATION CALCULATOR ━━━━━━━━━━━━━━━━━━━━━━━━
with tab_calc:
    st.markdown("### 🧮 Resource Valuation Calculator")
    st.markdown("Select a parcel and adjust assumptions to estimate projected resource value.")

    calc_c1, calc_c2 = st.columns([1, 2])

    with calc_c1:
        parcel_ids = df["id"].tolist()
        if parcel_ids:
            sel_id = st.selectbox("Select Parcel", parcel_ids, key="calc_parcel")
            parcel = df[df["id"] == sel_id].iloc[0]

            st.markdown("---")
            st.markdown("**Assumptions**")
            water_val_af = st.number_input("Water Rights Value ($/acre-ft/yr)", value=150.0, step=10.0, key="wv")
            gold_price_oz = st.number_input("Gold Price ($/oz)", value=2350.0, step=50.0, key="gp")
            timber_stumpage = st.number_input("Timber Stumpage ($/MBF)", value=350.0, step=25.0, key="ts")
            cap_rate = st.number_input("Cap Rate (%)", value=5.0, step=0.5, key="cr")
            holding_years = st.slider("Holding Period (yrs)", 1, 30, 10, key="hy")
        else:
            st.warning("No parcels available. Adjust filters.")
            parcel = None

    with calc_c2:
        if parcel is not None:
            # Water value
            water_annual = parcel["annual_recharge_af"] * water_val_af
            water_total = water_annual * holding_years

            # Timber value
            timber_mbf = parcel["timber_board_feet"] / 1000
            timber_val = timber_mbf * timber_stumpage

            # Gold / Mineral speculative value
            gold_multiplier = {"High": 0.15, "Medium": 0.05, "Low": 0.01}[parcel["gold_potential"]]
            gold_spec_val = parcel["acres"] * gold_multiplier * gold_price_oz * parcel["mineral_score"] / 10

            # Total resource value
            total_resource = water_total + timber_val + gold_spec_val
            total_with_land = total_resource + parcel["total_price"]
            roi = ((total_resource) / parcel["total_price"]) * 100 if parcel["total_price"] > 0 else 0

            # Display parcel info
            st.markdown(f"""
            <div style="background:#1a2236;border:1px solid #1e2d44;border-radius:10px;padding:1rem;margin-bottom:1rem;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;color:#00b4d8;font-weight:700;">{parcel['id']}</span>
                <span style="color:#8899aa;"> — {parcel['county']}, {parcel['state_name']}</span><br>
                <span style="color:#8899aa;font-size:0.85rem;">
                    {parcel['acres']:,.1f} acres &nbsp;|&nbsp; {fmt_price(parcel['total_price'])} &nbsp;|&nbsp;
                    Water: {parcel['water_score']:.1f} &nbsp;|&nbsp; Gold: {parcel['gold_potential']} &nbsp;|&nbsp;
                    Timber: {parcel['timber_score']:.1f}
                </span>
            </div>
            """, unsafe_allow_html=True)

            vc1, vc2, vc3, vc4 = st.columns(4)
            with vc1:
                render_metric_card("Water Value", fmt_price(water_total), "💧")
            with vc2:
                render_metric_card("Timber Value", fmt_price(timber_val), "🌲")
            with vc3:
                render_metric_card("Gold/Mineral", fmt_price(gold_spec_val), "⛏️")
            with vc4:
                render_metric_card("Est. ROI", f"{roi:.0f}%", "📈")

            st.markdown("")

            # Waterfall chart
            fig_val = go.Figure(go.Waterfall(
                name="Valuation",
                orientation="v",
                measure=["absolute","relative","relative","relative","total"],
                x=["Land Cost", f"Water ({holding_years}yr)", "Timber", "Gold/Mineral", "Total Value"],
                y=[parcel["total_price"], water_total, timber_val, gold_spec_val, 0],
                text=[fmt_price(parcel["total_price"]), fmt_price(water_total),
                      fmt_price(timber_val), fmt_price(gold_spec_val), fmt_price(total_with_land)],
                textposition="outside",
                connector={"line":{"color":"#1e2d44"}},
                increasing={"marker":{"color":"#06d6a0"}},
                decreasing={"marker":{"color":"#ef476f"}},
                totals={"marker":{"color":"#00b4d8"}},
            ))
            fig_val.update_layout(
                title=f"Projected Value Breakdown — {holding_years}-Year Hold",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8899aa", family="Inter"), title_font_size=14,
                yaxis=dict(gridcolor="#1e2d44"), height=380,
                margin=dict(l=40,r=20,t=50,b=30), showlegend=False,
            )
            st.plotly_chart(fig_val, use_container_width=True)

            st.caption("⚠️ Speculative estimates only. Gold/mineral values assume exploratory potential, not proven reserves. Water rights depend on state law and adjudication status. Always conduct professional due diligence.")


# ━━━━━━━━━━━━━━━━━━━━━━━━ TAB: ABOUT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_about:
    st.markdown("### About AquaForge Land Screener")
    st.markdown("""
AquaForge Land Screener is a prototype tool designed for land investors, resource prospectors, and due-diligence professionals who want to discover raw or vacant land parcels with untapped freshwater, mineral, and timber potential across the United States.

**How It Works**

The screener combines simulated parcel listing data with scoring models loosely inspired by public geological, hydrological, and forestry datasets. The **Water Potential Score** estimates the probability that a parcel sits above or near a productive aquifer or spring system, incorporating factors like USGS aquifer proximity, soil permeability patterns, and regional well-yield data. The **Mineral Score** weights proximity to known mineral occurrences (USGS MRDS-style data) and favorable geological formations. **Timber Score** reflects estimated standing timber density, species mix, and stumpage value potential.

**Data Sources (Production Roadmap)**

This prototype uses a synthetic dataset of 800 parcels generated with realistic geographic clustering. In production, the following public and commercial data feeds would be integrated:

- **Parcel Listings:** Regrid API, ATTOM Data Solutions, county GIS portals
- **Water / Aquifer:** USGS National Water Information System (NWIS), National Aquifer codes, state well logs
- **Minerals:** USGS MRDS (Mineral Resources Data System), USMIN mineral deposit database (mrdata.usgs.gov)
- **Timber:** USDA Forest Service FIA DataMart, FSGeodata Clearinghouse
- **Soils:** USDA NRCS Web Soil Survey (WSS)
- **Elevation:** USGS 3DEP (3D Elevation Program)

**Tech Stack:**  Python · Streamlit · Folium · Pandas · Plotly · NumPy
    """)

    st.markdown("""
**Deployment:**
```bash
# Local
pip install -r requirements.txt
streamlit run app.py

# Docker
docker build -t aquaforge .
docker run -p 8501:8501 aquaforge

# Streamlit Community Cloud
# Push to GitHub, connect at share.streamlit.io
```
    """)


# ──────────────────────────────────────────────────────────────────────────────
# DISCLAIMER FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    <strong>⚠️ Disclaimer:</strong> For informational and educational purposes only. Not financial, legal, or investment advice.
    Data is a mix of synthetic and public-domain sources. Scores are modeled estimates, not guarantees.
    Always verify with licensed professionals — geologists, hydrologists, real estate attorneys — and conduct
    full due diligence before any land acquisition. AquaForge is a prototype screening tool.
</div>
""", unsafe_allow_html=True)

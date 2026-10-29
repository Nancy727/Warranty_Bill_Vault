import streamlit as st
from database import get_mongo_client, ensure_indexes

# Import view functions
from pages.dashboard import show_dashboard
from pages.add_purchase import show_add_purchase
from pages.purchases import show_my_purchases
from pages.alerts import show_warranty_alerts
from pages.search import show_search
from pages.statistics import show_statistics
from pages.repair_predictor import show_repair_predictor

# Page Configuration
st.set_page_config(
    page_title="Warranty & Bill Vault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Uniform Dark UI
st.markdown(
    """
    <style>
    /* Hide Streamlit default multipage navigation to prevent double navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Main layout colors - Rich Uniform Dark Theme */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937 !important;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    /* Metric cards styling */
    div[data-testid="metric-container"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 16px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #60a5fa !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #94a3b8 !important;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
        border: 1px solid #334155 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
    }

    /* Popover & Expander dark styling */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* Radio button options in sidebar */
    div[data-testid="stRadio"] label {
        color: #e2e8f0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Branding & Navigation
st.sidebar.markdown("# 🛡️ Warranty Vault")
st.sidebar.markdown("*MongoDB College Mini-Project*")
st.sidebar.markdown("---")

# Navigation Selection (Query Performance removed)
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "➕ Add Purchase",
        "📦 My Purchases",
        "⚠️ Warranty Alerts",
        "🔍 Search",
        "📊 Statistics",
        "🔮 Repair Cost Predictor (ML)"
    ],
    index=0
)

# MongoDB Connection Check Status in Sidebar Footer
st.sidebar.markdown("---")
client, mongo_err = get_mongo_client()

if mongo_err:
    st.sidebar.error("🔴 MongoDB Disconnected")
    st.sidebar.caption(f"Error: {mongo_err}")
    st.sidebar.caption("Run local server: `mongodb://localhost:27017/`")
else:
    st.sidebar.success("🟢 MongoDB Connected")
    st.sidebar.caption("DB: `warranty_vault` | Collection: `products`")
    # Silently ensure text index
    ensure_indexes()

# Route to selected page module
if page == "🏠 Dashboard":
    show_dashboard()
elif page == "➕ Add Purchase":
    show_add_purchase()
elif page == "📦 My Purchases":
    show_my_purchases()
elif page == "⚠️ Warranty Alerts":
    show_warranty_alerts()
elif page == "🔍 Search":
    show_search()
elif page == "📊 Statistics":
    show_statistics()
elif page == "🔮 Repair Cost Predictor (ML)":
    show_repair_predictor()

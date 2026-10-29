import streamlit as st
import pandas as pd
from database import get_dashboard_metrics, get_products
from sample_data import seed_sample_data

def show_dashboard():
    st.title("🏠 Dashboard")
    st.caption("Overview of stored products, spending, and warranty statuses.")

    metrics, error = get_dashboard_metrics()
    if error:
        st.error(f"⚠️ Could not connect to MongoDB: {error}")
        st.info("💡 Make sure MongoDB Community Server is running locally on port 27017 (`mongodb://localhost:27017/`).")
        return

    # Metric Cards Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Products", f"{metrics['total_products']}")
    with col2:
        st.metric("Total Spent", f"₹{metrics['total_spent']:,.2f}")
    with col3:
        st.metric("Active Warranties", f"{metrics['active_count']}", delta="🟢 Active")
    with col4:
        st.metric("Expiring Soon", f"{metrics['expiring_soon_count']}", delta="🟡 Within 30d", delta_color="normal")
    with col5:
        st.metric("Expired", f"{metrics['expired_count']}", delta="🔴 Expired", delta_color="inverse")

    st.markdown("---")

    # Empty State Seeder Option
    if metrics["total_products"] == 0:
        st.info("📦 Your MongoDB `warranty_vault` database is currently empty!")
        if st.button("🚀 Seed Sample Demo Purchases (1-Click)", type="primary"):
            success, msg = seed_sample_data()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)
        return

    # Recent Purchases Section
    st.subheader("📋 Recent Purchases")
    products, err = get_products()

    if err:
        st.error(f"Error fetching purchases: {err}")
        return

    # Convert to pandas DataFrame for clean presentation
    table_data = []
    for p in products[:10]:  # Top 10 recent purchases
        table_data.append({
            "Product Name": p.get("name", "N/A"),
            "Category": p.get("category", "Other"),
            "Purchase Date": p.get("purchase_date", "N/A"),
            "Price (₹)": f"₹{p.get('price', 0):,.2f}",
            "Warranty Expiry": p.get("warranty_expiry_date", "N/A"),
            "Status": p.get("status_badge", "N/A")
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed Recent Cards
    st.markdown("#### Highlights")
    cols = st.columns(3)
    for idx, p in enumerate(products[:3]):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style="background-color: #1e293b; border-radius: 10px; padding: 16px; border: 1px solid #334155; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">
                    <h4 style="margin: 0 0 8px 0; color: #f8fafc;">{p.get('name')}</h4>
                    <p style="margin: 0; font-weight: bold; color: #60a5fa;">₹{p.get('price', 0):,.2f}</p>
                    <p style="margin: 4px 0; font-size: 0.88rem; color: #94a3b8;">Category: <b style="color: #e2e8f0;">{p.get('category')}</b></p>
                    <p style="margin: 4px 0; font-size: 0.88rem; color: #94a3b8;">Expiry: <span style="color: #e2e8f0;">{p.get('warranty_expiry_date')}</span></p>
                    <p style="margin: 8px 0 0 0; color: #f8fafc;">Status: <b>{p.get('status_badge')}</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    show_dashboard()

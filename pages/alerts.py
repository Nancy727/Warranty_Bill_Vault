import streamlit as st
from datetime import datetime, date
from database import get_products

def show_warranty_alerts():
    st.title("⚠️ Warranty Alerts")
    st.caption("Automatic warranty expiry checking for all stored products.")

    products, error = get_products()

    if error:
        st.error(f"⚠️ Could not retrieve products from MongoDB: {error}")
        return

    if not products:
        st.info("No products found in MongoDB vault.")
        return

    # Categorize products by warranty status
    expired_list = [p for p in products if p["computed_status"] == "Expired"]
    expiring_soon_list = [p for p in products if p["computed_status"] == "Expiring Soon"]
    active_list = [p for p in products if p["computed_status"] == "Active"]

    tab_expiring, tab_expired, tab_active = st.tabs([
        f"🟡 Expiring Soon ({len(expiring_soon_list)})",
        f"🔴 Expired ({len(expired_list)})",
        f"🟢 Active ({len(active_list)})"
    ])

    # 🟡 Expiring Soon Tab
    with tab_expiring:
        st.subheader("🟡 Expiring Within 30 Days")
        if not expiring_soon_list:
            st.success("🎉 No warranties expiring within the next 30 days!")
        else:
            for p in expiring_soon_list:
                days = p["days_left"]
                exp_date_str = p.get("warranty_expiry_date", "")
                try:
                    exp_formatted = datetime.strptime(exp_date_str, "%Y-%m-%d").strftime("%B %d, %Y")
                except Exception:
                    exp_formatted = exp_date_str

                message = f"Your **{p['name']}** warranty expires in **{days} day(s)** on **{exp_formatted}**."
                st.warning(f"⚠️ **Urgent**: {message}")
                
                with st.expander(f"View details for {p['name']}"):
                    st.write(f"- **Category**: {p.get('category')}")
                    st.write(f"- **Seller**: {p.get('seller', 'N/A')}")
                    st.write(f"- **Bill Number**: {p.get('bill_number', 'N/A')}")
                    st.write(f"- **Notes**: {p.get('notes', 'None')}")

    # 🔴 Expired Tab
    with tab_expired:
        st.subheader("🔴 Expired Warranties")
        if not expired_list:
            st.success("Great! No expired warranties found.")
        else:
            for p in expired_list:
                days_ago = abs(p["days_left"])
                exp_date_str = p.get("warranty_expiry_date", "")
                try:
                    exp_formatted = datetime.strptime(exp_date_str, "%Y-%m-%d").strftime("%B %d, %Y")
                except Exception:
                    exp_formatted = exp_date_str

                message = f"Your **{p['name']}** warranty expired **{days_ago} day(s) ago** on **{exp_formatted}**."
                st.error(f"❌ {message}")

                with st.expander(f"View details for {p['name']}"):
                    st.write(f"- **Category**: {p.get('category')}")
                    st.write(f"- **Seller**: {p.get('seller', 'N/A')}")
                    st.write(f"- **Bill Number**: {p.get('bill_number', 'N/A')}")
                    st.write(f"- **Notes**: {p.get('notes', 'None')}")

    # 🟢 Active Tab
    with tab_active:
        st.subheader("🟢 Active Warranties")
        if not active_list:
            st.info("No active warranties recorded.")
        else:
            for p in active_list:
                exp_date_str = p.get("warranty_expiry_date", "")
                try:
                    exp_formatted = datetime.strptime(exp_date_str, "%Y-%m-%d").strftime("%B %Y")
                except Exception:
                    exp_formatted = exp_date_str

                message = f"Your **{p['name']}** warranty is active until **{exp_formatted}** ({p['days_left']} days remaining)."
                st.info(f"✅ {message}")

if __name__ == "__main__":
    show_warranty_alerts()

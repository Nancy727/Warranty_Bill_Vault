import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_dashboard_metrics, get_category_aggregation, get_products

def show_statistics():
    st.title("📊 Statistics & Analytics")
    st.caption("Visual insights calculated directly via MongoDB Aggregation Pipelines.")

    st.markdown(
        """
        > 💡 **MongoDB Concept**: All category metrics on this page are computed using MongoDB **Aggregation Pipelines** (`$group`, `$sum`, `$avg`, `$sort`) via PyMongo `collection.aggregate()`.
        """
    )

    metrics, err = get_dashboard_metrics()
    if err:
        st.error(f"MongoDB Error: {err}")
        return

    # Overview Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Items", metrics["total_products"])
    m2.metric("Total Investment", f"₹{metrics['total_spent']:,.2f}")
    m3.metric("Active Warranties", metrics["active_count"])
    m4.metric("Expiring Soon", metrics["expiring_soon_count"])
    m5.metric("Expired", metrics["expired_count"])

    st.markdown("---")

    # Category Breakdown via Aggregation
    cat_agg, agg_err = get_category_aggregation()
    if agg_err:
        st.error(f"Error executing aggregation pipeline: {agg_err}")
        return

    if not cat_agg:
        st.info("No data available to generate statistics.")
        return

    # Format aggregation results into DataFrame
    cat_data = []
    for item in cat_agg:
        cat_data.append({
            "Category": item["_id"] if item["_id"] else "Uncategorized",
            "Total Spent (₹)": float(item["total_spent"]),
            "Product Count": int(item["product_count"]),
            "Average Price (₹)": float(item["avg_price"])
        })
    df_cat = pd.DataFrame(cat_data)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💰 Spending by Category")
        fig_bar = px.bar(
            df_cat,
            x="Category",
            y="Total Spent (₹)",
            color="Category",
            text_auto=".2s",
            title="Total Amount Spent per Category (MongoDB $group)"
        )
        fig_bar.update_layout(showlegend=False, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("📦 Products per Category")
        fig_pie = px.pie(
            df_cat,
            names="Category",
            values="Product Count",
            title="Product Count Distribution per Category",
            hole=0.4
        )
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Warranty Status Breakdown Chart
    st.subheader("🛡️ Warranty Status Breakdown")
    status_df = pd.DataFrame({
        "Status": ["Active 🟢", "Expiring Soon 🟡", "Expired 🔴"],
        "Count": [metrics["active_count"], metrics["expiring_soon_count"], metrics["expired_count"]]
    })

    fig_status = px.pie(
        status_df,
        names="Status",
        values="Count",
        color="Status",
        color_discrete_map={
            "Active 🟢": "#22c55e",
            "Expiring Soon 🟡": "#eab308",
            "Expired 🔴": "#ef4444"
        },
        title="Warranty Expiry Status Distribution"
    )
    fig_status.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_status, use_container_width=True)

    # Detailed Aggregation Table (for Viva Explanation)
    with st.expander("🔍 View Raw MongoDB Aggregation Pipeline Results (For Viva)"):
        st.markdown("**Executed MongoDB Pipeline:**")
        st.code(
            """
pipeline = [
    {
        "$group": {
            "_id": "$category",
            "total_spent": {"$sum": "$price"},
            "product_count": {"$sum": 1},
            "avg_price": {"$avg": "$price"}
        }
    },
    {
        "$sort": {"total_spent": -1}
    }
]
results = collection.aggregate(pipeline)
            """,
            language="python"
        )
        st.dataframe(df_cat, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    show_statistics()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date
from database import (
    predict_repair_cost,
    train_repair_cost_model,
    get_all_repairs,
    insert_repair_record,
    delete_repair_record,
    seed_default_repair_data,
    get_repair_cost_aggregation,
    get_products,
    CATEGORIES
)

def show_repair_predictor():
    st.title("🔮 Repair Cost Predictor (Linear Regression)")
    st.caption("Predict estimated product repair cost based on product age using Machine Learning & MongoDB.")

    # Top Concept Callout for College Viva
    st.markdown(
        """
        > 💡 **College Project Concept**:
        > - **Machine Learning**: Simple Linear Regression ($y = mx + c$) predicting **Repair Cost** ($y$) based on **Product Age in Months** ($x$).
        > - **MongoDB Database**: Historical repair data is stored in MongoDB (`repair_history` collection).
        > - **CRUD & Aggregation**: Full CRUD operations + MongoDB `$group` aggregation pipeline for category-wise repair costs.
        """
    )

    tab_predict, tab_aggregate, tab_crud = st.tabs([
        "🔮 Predict Repair Cost (ML)",
        "📊 Simple Aggregate Function",
        "📝 Repair Data & CRUD Operations"
    ])

    # ==========================================
    # Tab 1: Predict Repair Cost (Linear Regression)
    # ==========================================
    with tab_predict:
        st.subheader("🤖 Predict Repair Cost from Product Age")

        # Option to select an existing product or enter age manually
        products, _ = get_products()
        use_vault_product = False
        selected_prod_age = 12

        col_mode, _ = st.columns([2, 1])
        with col_mode:
            input_mode = st.radio(
                "Choose Input Method:",
                ["Enter Product Age Manually", "Select a Product from My Vault"],
                horizontal=True
            )

        if input_mode == "Select a Product from My Vault" and products:
            prod_names = [f"{p.get('name')} (Purchased: {p.get('purchase_date')})" for p in products]
            chosen_idx = st.selectbox("Select Stored Product:", range(len(prod_names)), format_func=lambda i: prod_names[i])
            chosen_product = products[chosen_idx]

            # Calculate age in months from purchase_date to today
            p_date_str = chosen_product.get("purchase_date", "")
            try:
                p_dt = datetime.strptime(p_date_str, "%Y-%m-%d").date()
                today = date.today()
                # Age in months
                computed_months = max(1, (today.year - p_dt.year) * 12 + (today.month - p_dt.month))
            except Exception:
                computed_months = 12

            st.info(f"📅 **{chosen_product.get('name')}** was purchased on `{p_date_str}`. Computed Age: **{computed_months} month(s)**.")
            age_input = st.number_input("Product Age in Months:", min_value=1, max_value=120, value=int(computed_months))
        else:
            age_input = st.slider("Product Age (in Months):", min_value=1, max_value=120, value=18, step=1)

        # Run Prediction
        pred_res = predict_repair_cost(age_input)
        pred_cost = pred_res["predicted_cost"]
        slope = pred_res["slope"]
        intercept = pred_res["intercept"]
        r2 = pred_res["r2_score"]
        repairs_data = pred_res["training_data"]

        # Results Display Row
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Predicted Repair Cost", f"₹{pred_cost:,.2f}", delta=f"{age_input} mos old")
        m2.metric("Regression Slope (m)", f"₹{slope:,.2f} / mo")
        m3.metric("Base Cost / Intercept (c)", f"₹{intercept:,.2f}")
        m4.metric("Model R² Score (Fit)", f"{r2:.4f}")

        st.success(f"📐 **Linear Regression Formula**: `{pred_res['formula_str']}`")
        st.caption(f"Meaning: For every 1 additional month of age, the estimated repair cost increases by **₹{slope:,.2f}**.")

        # Interactive Regression Plot (Plotly)
        st.markdown("#### 📈 Linear Regression Line & Training Data Points")
        if repairs_data:
            df_plot = pd.DataFrame(repairs_data)
            x_train = df_plot["age_months"]
            y_train = df_plot["repair_cost"]

            # Generate regression line coordinates
            x_line = np.linspace(0, max(max(x_train), age_input) + 6, 100)
            y_line = slope * x_line + intercept

            fig = go.Figure()

            # Scatter points of historical repairs
            fig.add_trace(go.Scatter(
                x=x_train,
                y=y_train,
                mode="markers",
                name="Historical Repairs (MongoDB)",
                marker=dict(size=10, color="#2563eb", symbol="circle"),
                text=df_plot["product_name"],
                hovertemplate="<b>%{text}</b><br>Age: %{x} months<br>Repair Cost: ₹%{y:,.2f}<extra></extra>"
            ))

            # Regression line
            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name=f"Linear Fit (y = {slope:.1f}x + {intercept:.1f})",
                line=dict(color="#10b981", width=3, dash="dash")
            ))

            # User's predicted point
            fig.add_trace(go.Scatter(
                x=[age_input],
                y=[pred_cost],
                mode="markers",
                name=f"Your Query ({age_input} mos: ₹{pred_cost:,.0f})",
                marker=dict(size=14, color="#ef4444", symbol="star")
            ))

            fig.update_layout(
                title=f"Repair Cost vs Product Age (Linear Regression)",
                xaxis_title="Product Age (Months)",
                yaxis_title="Repair Cost (₹ INR)",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # Tab 2: Simple MongoDB Aggregation Pipeline
    # ==========================================
    with tab_aggregate:
        st.subheader("📊 MongoDB Aggregation: Average Repair Cost by Category")
        st.markdown(
            """
            > 💡 **Viva Explanation**:
            > This demonstrates a clean MongoDB **Aggregation Pipeline** using the `$group` stage with `$avg`, `$sum`, `$min`, and `$max` accumulators.
            """
        )

        # Show Aggregation Pipeline Code
        st.code(
            """
# Simple MongoDB Aggregation Pipeline
pipeline = [
    {
        "$group": {
            "_id": "$category",
            "average_repair_cost": {"$avg": "$repair_cost"},
            "total_repairs": {"$sum": 1},
            "min_repair_cost": {"$min": "$repair_cost"},
            "max_repair_cost": {"$max": "$repair_cost"}
        }
    },
    {
        "$sort": {"average_repair_cost": -1}
    }
]
results = db["repair_history"].aggregate(pipeline)
            """,
            language="python"
        )

        agg_results, agg_err = get_repair_cost_aggregation()
        if agg_err:
            st.error(f"Error running aggregation: {agg_err}")
        elif not agg_results:
            st.info("No repair records available to aggregate. Add records in the next tab or seed demo data.")
        else:
            agg_table = []
            for r in agg_results:
                agg_table.append({
                    "Category": r["_id"] if r["_id"] else "Other",
                    "Average Repair Cost (₹)": f"₹{r.get('average_repair_cost', 0):,.2f}",
                    "Total Repairs Count": r.get("total_repairs", 0),
                    "Min Cost (₹)": f"₹{r.get('min_repair_cost', 0):,.2f}",
                    "Max Cost (₹)": f"₹{r.get('max_repair_cost', 0):,.2f}"
                })
            df_agg = pd.DataFrame(agg_table)
            st.dataframe(df_agg, use_container_width=True, hide_index=True)

    # ==========================================
    # Tab 3: Simple CRUD for Repair Records
    # ==========================================
    with tab_crud:
        st.subheader("📝 Manage Repair Records in MongoDB (CRUD)")
        st.caption("Demonstrates insert_one(), find(), and delete_one() on the `repair_history` collection.")

        # Add New Repair Record (CREATE: insert_one)
        with st.expander("➕ Add New Repair Record (`insert_one`)", expanded=False):
            with st.form("add_repair_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    r_name = st.text_input("Product Name *", placeholder="e.g. Dell Monitor")
                    r_cat = st.selectbox("Category *", CATEGORIES)
                with c2:
                    r_age = st.number_input("Product Age (in Months) *", min_value=1, max_value=240, value=12)
                    r_cost = st.number_input("Actual Repair Cost (₹) *", min_value=100.0, step=100.0, value=2500.0)
                r_issue = st.text_input("Issue / Repair Description", placeholder="e.g. Screen flickering / backlight")

                submit_repair = st.form_submit_button("➕ Save Repair Record to MongoDB", type="primary")

                if submit_repair:
                    if not r_name.strip():
                        st.error("Product name is required!")
                    else:
                        ins_id, err = insert_repair_record(r_name, r_cat, r_age, r_cost, r_issue)
                        if err:
                            st.error(f"Insert failed: {err}")
                        else:
                            st.success(f"✅ Record inserted with MongoDB `_id`: `{ins_id}`!")
                            st.rerun()

        # View and Delete Records (READ: find & DELETE: delete_one)
        repairs, fetch_err = get_all_repairs()
        if fetch_err:
            st.error(f"Error loading repairs: {fetch_err}")
            return

        st.markdown(f"**Total Records in MongoDB**: `{len(repairs)}`")

        col_seed, _ = st.columns([2, 3])
        with col_seed:
            if st.button("🔄 Reset / Re-Seed Default Repair Data"):
                seed_default_repair_data()
                st.success("Default repair records re-seeded!")
                st.rerun()

        if repairs:
            # Table display
            table_rows = []
            for r in repairs:
                table_rows.append({
                    "Product": r.get("product_name"),
                    "Category": r.get("category"),
                    "Age (Months)": r.get("age_months"),
                    "Repair Cost (₹)": f"₹{r.get('repair_cost', 0):,.2f}",
                    "Issue Description": r.get("issue_description", ""),
                    "MongoDB ID": r.get("_id_str")
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

            # Delete popover
            with st.popover("🗑️ Delete a Repair Record (`delete_one`)"):
                del_id = st.selectbox(
                    "Select Record to Delete:",
                    [r["_id_str"] for r in repairs],
                    format_func=lambda x: next((f"{r['product_name']} ({r['age_months']} mos: ₹{r['repair_cost']})" for r in repairs if r["_id_str"] == x), x)
                )
                if st.button("Confirm Delete", type="primary"):
                    ok, err = delete_repair_record(del_id)
                    if ok:
                        st.success("Record deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {err}")

if __name__ == "__main__":
    show_repair_predictor()

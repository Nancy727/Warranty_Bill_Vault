import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_products, update_product, delete_product, get_product_by_id, CATEGORIES

STATUS_OPTIONS = ["All", "Active", "Expiring Soon", "Expired"]
CATEGORY_OPTIONS = ["All"] + CATEGORIES

def show_my_purchases():
    st.title("📦 My Purchases")
    st.caption("View, search, filter, edit, and delete purchases stored in MongoDB.")

    # Fetch initial product list for year extraction
    all_products, err = get_products()

    if err:
        st.error(f"⚠️ Could not load products from MongoDB: {err}")
        return

    # Extract available purchase years for filter
    years = set()
    for p in all_products:
        p_date = str(p.get("purchase_date", ""))
        if "-" in p_date:
            years.add(p_date.split("-")[0])
    year_options = ["All"] + sorted(list(years), reverse=True)

    # Filtering Controls Toolbar
    col_search, col_cat, col_stat, col_yr = st.columns([3, 2, 2, 2])
    
    with col_search:
        search_query = st.text_input("🔍 Search product name...", placeholder="Type product name, seller, etc.")
    with col_cat:
        selected_category = st.selectbox("Category Filter", CATEGORY_OPTIONS)
    with col_stat:
        selected_status = st.selectbox("Status Filter", STATUS_OPTIONS)
    with col_yr:
        selected_year = st.selectbox("Purchase Year", year_options)

    # Fetch filtered products
    filtered_products, fetch_err = get_products(
        category_filter=selected_category,
        status_filter=selected_status,
        year_filter=selected_year,
        search_term=search_query if search_query else None
    )

    if fetch_err:
        st.error(f"Error filtering products: {fetch_err}")
        return

    st.markdown(f"**Found {len(filtered_products)} product(s)**")

    if not filtered_products:
        st.info("No purchases match the selected filter criteria.")
        return

    # Display products in clean modern cards with Edit / Delete actions
    for p in filtered_products:
        doc_id = p["_id_str"]
        with st.container():
            st.markdown(
                f"""
                <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">{p.get('name')}</h3>
                        <span style="font-size: 0.95rem; font-weight: 600;">{p.get('status_badge')}</span>
                    </div>
                    <div style="display: flex; gap: 24px; margin-top: 10px; color: #cbd5e1; font-size: 0.92rem;">
                        <span>🏷️ Category: <b style="color: #f8fafc;">{p.get('category')}</b></span>
                        <span>💰 Price: <b style="color: #60a5fa;">₹{p.get('price', 0):,.2f}</b></span>
                        <span>📅 Purchased: <b style="color: #f8fafc;">{p.get('purchase_date')}</b></span>
                        <span>⏳ Expiry: <b style="color: #f8fafc;">{p.get('warranty_expiry_date')}</b></span>
                    </div>
                    <div style="margin-top: 8px; color: #94a3b8; font-size: 0.88rem;">
                        <span>🏢 Seller: {p.get('seller', 'N/A')}</span> | 
                        <span>🧾 Bill #: {p.get('bill_number', 'N/A')}</span> | 
                        <span>⏱️ Duration: {p.get('warranty_duration_months', 0)} mos</span>
                    </div>
                    {f'<div style="margin-top: 6px; font-style: italic; color: #94a3b8; font-size: 0.85rem;">📝 Notes: {p.get("notes")}</div>' if p.get('notes') else ''}
                </div>
                """,
                unsafe_allow_html=True
            )

            col_edit, col_del, _ = st.columns([1, 1, 6])
            
            with col_edit:
                with st.popover("✏️ Edit"):
                    st.markdown(f"#### Edit `{p.get('name')}`")
                    with st.form(f"edit_form_{doc_id}"):
                        new_name = st.text_input("Product Name", value=p.get("name", ""))
                        new_category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(p.get("category")) if p.get("category") in CATEGORIES else 0)
                        new_price = st.number_input("Price (₹)", value=float(p.get("price", 0.0)))
                        
                        p_date_obj = datetime.strptime(p.get("purchase_date"), "%Y-%m-%d").date() if p.get("purchase_date") else date.today()
                        new_p_date = st.date_input("Purchase Date", value=p_date_obj)
                        
                        new_seller = st.text_input("Seller", value=p.get("seller", ""))
                        new_bill = st.text_input("Bill Number", value=p.get("bill_number", ""))
                        new_dur = st.number_input("Warranty Duration (Months)", value=int(p.get("warranty_duration_months", 12)))
                        new_notes = st.text_area("Notes", value=p.get("notes", ""))

                        update_btn = st.form_submit_button("Update Product", type="primary")

                        if update_btn:
                            update_payload = {
                                "name": new_name.strip(),
                                "category": new_category,
                                "price": float(new_price),
                                "purchase_date": new_p_date.strftime("%Y-%m-%d"),
                                "seller": new_seller.strip(),
                                "bill_number": new_bill.strip(),
                                "warranty_duration_months": int(new_dur),
                                "notes": new_notes.strip()
                            }
                            ok, update_err = update_product(doc_id, update_payload)
                            if ok:
                                st.success("Updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Update failed: {update_err}")

            with col_del:
                with st.popover("🗑️ Delete"):
                    st.warning(f"Are you sure you want to delete **'{p.get('name')}'**?")
                    st.caption("This operation will invoke PyMongo `delete_one()`.")
                    if st.button("Confirm Delete", key=f"confirm_del_{doc_id}", type="primary"):
                        ok, del_err = delete_product(doc_id)
                        if ok:
                            st.success("Deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {del_err}")

            st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px dashed #334155;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    show_my_purchases()

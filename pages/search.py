import streamlit as st
import json
from bson import json_util
from database import search_products_text_index, ensure_indexes

def show_search():
    st.title("🔍 Search Vault")
    st.caption("Perform fast text search across product names, categories, sellers, and bill numbers.")

    # MongoDB Text Index status banner
    st.markdown(
        """
        > 💡 **MongoDB Concept**: Search is powered by a MongoDB **Compound Text Index** on `name`, `category`, `seller`, and `bill_number` using the PyMongo `$text` operator.
        """
    )

    query = st.text_input("Enter search query:", placeholder="e.g. Sony, Headphones, Amazon, INV-2026, Appliances...")

    col_btn, col_idx = st.columns([2, 3])
    with col_btn:
        search_clicked = st.button("🔎 Execute Search", type="primary", use_container_width=True)
    with col_idx:
        if st.button("⚡ Ensure MongoDB Text Index (`create_index`)", use_container_width=True):
            ok, msg = ensure_indexes()
            if ok:
                st.success("MongoDB compound text index verified on `products` collection!")
            else:
                st.error(f"Index error: {msg}")

    if query or search_clicked:
        if not query.strip():
            st.warning("Please enter a search term.")
            return

        with st.spinner("Searching MongoDB..."):
            results, error = search_products_text_index(query.strip())

        if error:
            st.error(f"MongoDB search error: {error}")
            return

        st.markdown(f"### Results for *'{query}'* ({len(results)} found)")

        if not results:
            st.info("No matching documents found in MongoDB.")
            return

        show_raw_json = st.checkbox("⚙️ Show raw MongoDB BSON document preview (Viva Demo)")

        for doc in results:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; border-left: 4px solid #3b82f6; border: 1px solid #334155; padding: 14px 18px; border-radius: 6px; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">
                        <h4 style="margin:0 0 6px 0; color: #f8fafc;">{doc.get('name')}</h4>
                        <div style="color: #cbd5e1; font-size: 0.9rem;">
                            <b>Category:</b> {doc.get('category')} | 
                            <b>Price:</b> <span style="color: #60a5fa; font-weight: bold;">₹{doc.get('price', 0):,.2f}</span> | 
                            <b>Seller:</b> {doc.get('seller', 'N/A')} | 
                            <b>Bill #:</b> {doc.get('bill_number', 'N/A')}
                        </div>
                        <div style="margin-top: 6px; font-size: 0.88rem; color: #94a3b8;">
                            <b>Warranty Expiry:</b> <span style="color: #e2e8f0;">{doc.get('warranty_expiry_date')}</span> ({doc.get('status_badge')})
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if show_raw_json:
                    # Clean up _id for json serialization
                    doc_copy = dict(doc)
                    if "_id" in doc_copy:
                        doc_copy["_id"] = str(doc_copy["_id"])
                    st.code(json.dumps(doc_copy, indent=2, default=str), language="json")

if __name__ == "__main__":
    show_search()

import streamlit as st
from datetime import date, datetime
from database import insert_product, calculate_expiry_date

CATEGORIES = [
    "Electronics",
    "Appliances",
    "Furniture",
    "Clothing",
    "Accessories",
    "Other"
]

def show_add_purchase():
    st.title("➕ Add Purchase")
    st.caption("Register a new product with warranty details into MongoDB.")

    with st.form("add_purchase_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name *", placeholder="e.g. Sony WH-1000XM5 Headphones")
            category = st.selectbox("Category *", CATEGORIES)
            price = st.number_input("Price (₹) *", min_value=0.0, step=100.0, value=0.0)
            purchase_date = st.date_input("Purchase Date *", value=date.today())

        with col2:
            seller = st.text_input("Seller / Retailer", placeholder="e.g. Amazon, Croma, Reliance Digital")
            bill_number = st.text_input("Bill / Invoice Number", placeholder="e.g. INV-2026-9901")
            duration_months = st.number_input("Warranty Duration (Months) *", min_value=0, max_value=240, value=12)
            
            # Automatically calculate initial expiry date based on purchase_date + duration_months
            default_exp = calculate_expiry_date(purchase_date, duration_months)
            expiry_date = st.date_input("Warranty Expiry Date", value=default_exp)

        notes = st.text_area("Notes / Warranty Terms", placeholder="Add extra details, support email, claim process, etc.")

        submitted = st.form_submit_button("➕ Save Purchase to Vault", type="primary", use_container_width=True)

        if submitted:
            # Basic validations
            if not name.strip():
                st.error("❌ Product Name cannot be empty!")
                return

            if price < 0:
                st.error("❌ Price cannot be negative!")
                return

            if duration_months < 0:
                st.error("❌ Warranty Duration cannot be negative!")
                return

            if not purchase_date:
                st.error("❌ Purchase Date is required!")
                return

            # Construct product document
            product_doc = {
                "name": name.strip(),
                "category": category,
                "price": float(price),
                "purchase_date": purchase_date.strftime("%Y-%m-%d"),
                "seller": seller.strip(),
                "bill_number": bill_number.strip(),
                "warranty_duration_months": int(duration_months),
                "warranty_expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "notes": notes.strip()
            }

            # Call PyMongo insert_one() wrapper
            inserted_id, error = insert_product(product_doc)

            if error:
                st.error(f"❌ Failed to insert into MongoDB: {error}")
            else:
                st.success(f"✅ Product **'{name}'** added successfully! (MongoDB `_id`: `{inserted_id}`)")
                st.toast("Product added to MongoDB!", icon="🎉")

if __name__ == "__main__":
    show_add_purchase()

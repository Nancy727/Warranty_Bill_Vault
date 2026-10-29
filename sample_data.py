"""
Sample data seeder for Warranty & Bill Vault.
Easily seed demo products into MongoDB for testing and Viva demonstration.
"""
from database import get_collection, calculate_expiry_date
from datetime import date

SAMPLE_PRODUCTS = [
    {
        "name": "Sony WH-1000XM5 Noise Canceling Headphones",
        "category": "Electronics",
        "price": 29990.0,
        "purchase_date": "2026-02-15",
        "seller": "Amazon India",
        "bill_number": "INV-SONY-2026-091",
        "warranty_duration_months": 24,
        "warranty_expiry_date": "2028-02-15",
        "notes": "Includes 2-year manufacturer warranty with accidental damage protection."
    },
    {
        "name": "HP Omen 16 Gaming Laptop",
        "category": "Electronics",
        "price": 118000.0,
        "purchase_date": "2026-01-10",
        "seller": "HP World Store",
        "bill_number": "HP-BL-99201",
        "warranty_duration_months": 36,
        "warranty_expiry_date": "2029-01-10",
        "notes": "3 Years Extended On-Site Warranty registered online."
    },
    {
        "name": "LG 260L Double Door Refrigerator",
        "category": "Appliances",
        "price": 34990.0,
        "purchase_date": "2025-10-15",
        "seller": "Reliance Digital",
        "bill_number": "RD-DEL-4412",
        "warranty_duration_months": 12,
        "warranty_expiry_date": "2026-10-15",
        "notes": "Compressor has 10 year extended warranty badge."
    },
    {
        "name": "Philips Air Fryer HD9252/90",
        "category": "Appliances",
        "price": 8499.0,
        "purchase_date": "2025-09-25",
        "seller": "Flipkart",
        "bill_number": "FK-INV-883192",
        "warranty_duration_months": 13,
        "warranty_expiry_date": "2026-10-25",
        "notes": "2 Year warranty claim code attached with invoice."
    },
    {
        "name": "Ergonomic Mesh High Back Office Chair",
        "category": "Furniture",
        "price": 14200.0,
        "purchase_date": "2023-05-10",
        "seller": "Featherlite Furniture",
        "bill_number": "FL-BL-2023-55",
        "warranty_duration_months": 12,
        "warranty_expiry_date": "2024-05-10",
        "notes": "Hydraulic lift replaced once under warranty."
    },
    {
        "name": "Samsung 55 Inch 4K Smart QLED TV",
        "category": "Electronics",
        "price": 64990.0,
        "purchase_date": "2024-01-20",
        "seller": "Croma Electronics",
        "bill_number": "CR-MUM-7721",
        "warranty_duration_months": 24,
        "warranty_expiry_date": "2026-01-20",
        "notes": "Panel warranty expired."
    },
    {
        "name": "Apple Watch Series 9 GPS",
        "category": "Accessories",
        "price": 41900.0,
        "purchase_date": "2025-10-28",
        "seller": "Imagine Apple Store",
        "bill_number": "IMG-BL-33019",
        "warranty_duration_months": 12,
        "warranty_expiry_date": "2026-10-28",
        "notes": "AppleCare+ active."
    }
]

def seed_sample_data():
    collection, error = get_collection()
    if error:
        return False, error

    # Insert documents
    try:
        # Check if already seeded
        if collection.count_documents({}) > 0:
            return False, "Database already has records! Clear or delete existing records to re-seed."

        result = collection.insert_many(SAMPLE_PRODUCTS)
        return True, f"Successfully seeded {len(result.inserted_ids)} sample products into MongoDB!"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    success, msg = seed_sample_data()
    print(msg)

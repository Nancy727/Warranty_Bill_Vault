# 🛡️ Warranty & Bill Vault

A clean, modern **Warranty & Bill Vault** web application built with **Python, Streamlit, and MongoDB (PyMongo)**. Designed specifically as a college MongoDB mini-project.

---

## 📌 Features

- **🏠 Dashboard**: Overview cards for Total Products, Total Spent, Active, Expiring Soon, and Expired Warranties with Recent Purchases table.
- **➕ Add Purchase**: Easy form to register new purchases with validation, cost, seller, bill number, and automatic warranty expiry calculation.
- **📦 My Purchases**: Complete product inventory with filters (Category, Status, Year), real-time search, inline edit modal (`update_one`), and delete with confirmation (`delete_one`).
- **⚠️ Warranty Alerts**: Automatic categorization of warranties into 🔴 Expired, 🟡 Expiring within 30 days, and 🟢 Active.
- **🔍 Search Vault**: Compound text search across product names, categories, sellers, and bill numbers using MongoDB `$text` text indexing.
- **📊 Statistics & Aggregation**: Category-wise spending breakdown, pie charts, and status distributions calculated via **MongoDB Aggregation Pipelines**.
- **🔮 Repair Cost Predictor (Linear Regression)**: Simple ML regression model predicting **Repair Cost** based on **Product Age in Months** ($y = mx + c$), with MongoDB-backed historical repairs (`repair_history` collection) and category aggregation.

---

## 🛠️ Technology Stack

- **Frontend & App Framework**: Python + Streamlit
- **Database**: MongoDB Community Server (Local `mongodb://localhost:27017/`)
- **Database Driver**: PyMongo (`pymongo`)
- **Data & Charts**: Pandas, Plotly Express

---

## 🚀 How to Run the Application

### 1. Prerequisites
Ensure you have **Python 3.9+** and **MongoDB Community Server** installed and running on your system.

Start MongoDB local server (if not already running):
```bash
# Windows MongoDB service starts automatically, or start via Command Prompt / PowerShell:
net start MongoDB
```

### 2. Install Dependencies
Open terminal/PowerShell in the project directory:
```bash
pip install -r requirements.txt
```

### 3. Launch Streamlit App
Run the following command:
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
warranty-bill-vault/
│
├── app.py                  # Main Streamlit application launcher & sidebar navigation
├── database.py             # PyMongo connection, CRUD, Aggregation, Explain & Schema Validation
├── sample_data.py          # 1-Click sample data seeder for testing
├── requirements.txt        # Python package dependencies
│
└── pages/                  # Modular view modules for each sidebar navigation tab
    ├── dashboard.py        # Summary metrics & recent items
    ├── add_purchase.py     # New purchase form & validation
    ├── purchases.py        # Full inventory with filters, edit, and delete
    ├── alerts.py           # Expiry alert tabs
    ├── search.py           # MongoDB Text Index search view
    ├── statistics.py       # Aggregation Pipeline analytics & charts
    └── repair_predictor.py # Linear Regression Prediction (Repair Cost by Age), Simple CRUD & Aggregation
```

---

## 🎓 MongoDB Viva Q&A Guide

This project demonstrates 12 key MongoDB database concepts. Here are code examples to help you answer questions during your viva:

### 1. `insert_one()` - Document Insertion
**Where used**: `database.py -> insert_product()`
```python
result = collection.insert_one(product_data)
inserted_id = str(result.inserted_id)
```

### 2. `find()` - Document Querying & Filtering
**Where used**: `database.py -> get_products()`
```python
cursor = collection.find({"category": "Electronics"}).sort("purchase_date", -1)
products_list = list(cursor)
```

### 3. `find_one()` - Finding a Single Document
**Where used**: `database.py -> get_product_by_id()`
```python
document = collection.find_one({"_id": ObjectId(doc_id)})
```

### 4. `update_one()` - Document Modification
**Where used**: `database.py -> update_product()`
```python
result = collection.update_one(
    {"_id": ObjectId(doc_id)},
    {"$set": {"price": 25000.0, "notes": "Updated warranty term"}}
)
```

### 5. `delete_one()` - Document Removal
**Where used**: `database.py -> delete_product()`
```python
result = collection.delete_one({"_id": ObjectId(doc_id)})
```

### 6. `create_index()` - Text & Compound Indexing
**Where used**: `database.py -> ensure_indexes() / ensure_category_index()`
```python
# Text Index
collection.create_index([("name", pymongo.TEXT), ("category", pymongo.TEXT)], name="text_search_index")

# Compound Index for Covered Query
collection.create_index([("category", 1), ("name", 1)], name="category_name_idx")
```

### 7. `list_indexes()` - Listing Active Indexes
**Where used**: `database.py -> get_collection_indexes()`
```python
indexes = list(collection.list_indexes())
```

### 8. `explain("executionStats")` - Query Execution Plan Analysis
**Where used**: `database.py -> run_explain_comparison()`
```python
cursor = collection.find({"category": "Electronics"}).hint([("category", 1), ("name", 1)])
explain_output = cursor.explain("executionStats")
# Key metrics: executionTimeMillis, totalDocsExamined, totalKeysExamined
```

### 9. Covered Queries - Zero-Disk-Read Queries
**Where used**: `database.py -> demonstrate_covered_query()`
```python
# Query covered completely by index (totalDocsExamined = 0)
cursor = collection.find(
    {"category": "Electronics"},                # Filter on indexed field
    {"_id": 0, "category": 1, "name": 1}         # Projection only indexed fields, exclude _id
).hint([("category", 1), ("name", 1)])
```

### 10. `$jsonSchema` - Collection Validation Rules
**Where used**: `database.py -> apply_schema_validation()`
```python
schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "category", "price", "purchase_date"],
        "properties": {
            "name": {"bsonType": "string"},
            "category": {"bsonType": "string"},
            "price": {"bsonType": ["double", "int", "long", "decimal"], "minimum": 0},
            "purchase_date": {"bsonType": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}
        }
    }
}
# Apply validation without dropping collection
db.command("collMod", "products", validator=schema, validationLevel="moderate")
```

### 11. `$text` Search Operator
**Where used**: `database.py -> search_products_text_index()`
```python
cursor = collection.find({"$text": {"$search": "Sony Headphones"}})
```

### 12. `aggregate()` - Aggregation Pipelines ($group, $sum, $avg, $sort)
**Where used**: `database.py -> get_category_aggregation()`
```python
pipeline = [
    {"$group": {"_id": "$category", "total_spent": {"$sum": "$price"}, "avg_price": {"$avg": "$price"}}},
    {"$sort": {"total_spent": -1}}
]
results = list(collection.aggregate(pipeline))
```

### 13. Simple Linear Regression - Predicting Repair Cost by Product Age
**Where used**: `database.py -> train_repair_cost_model() & predict_repair_cost()`
```python
from sklearn.linear_model import LinearRegression
import numpy as np

# X = Product Age in Months, y = Historical Repair Cost in INR
X = np.array([[6], [12], [18], [24], [36], [48]])
y = np.array([850, 1400, 2900, 3400, 6200, 8900])

model = LinearRegression()
model.fit(X, y)

# Prediction formula: y = mx + c
predicted_cost = model.predict([[24]])[0]  # Predict for 24-month-old item
```

### 14. Simple Aggregate Function on Repairs
**Where used**: `database.py -> get_repair_cost_aggregation()`
```python
pipeline = [
    {
        "$group": {
            "_id": "$category",
            "average_repair_cost": {"$avg": "$repair_cost"},
            "total_repairs": {"$sum": 1}
        }
    }
]
results = list(db["repair_history"].aggregate(pipeline))
```

---

## 🔒 Database Details

- **Database Name**: `warranty_vault`
- **Collection Name**: `products`
- **Connection URI**: `mongodb://localhost:27017/`


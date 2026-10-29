import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "warranty_vault"
COLLECTION_NAME = "products"
REPAIR_COLLECTION_NAME = "repair_history"

CATEGORIES = [
    "Electronics",
    "Appliances",
    "Furniture",
    "Clothing",
    "Accessories",
    "Other"
]

@st.cache_resource
def get_mongo_client():
    """
    Creates and caches the PyMongo MongoClient instance.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Quick check if server is reachable
        client.admin.command('ping')
        return client, None
    except Exception as e:
        return None, str(e)

def get_collection():
    """
    Returns the MongoDB products collection.
    """
    client, error = get_mongo_client()
    if error or client is None:
        return None, error
    db = client[DB_NAME]
    return db[COLLECTION_NAME], None

def get_repair_collection():
    """
    Returns the MongoDB repair_history collection.
    """
    client, error = get_mongo_client()
    if error or client is None:
        return None, error
    db = client[DB_NAME]
    return db[REPAIR_COLLECTION_NAME], None

def ensure_indexes():
    """
    Demonstrates MongoDB create_index() operation.
    Creates a compound text index on product fields for efficient text search.
    """
    collection, error = get_collection()
    if error or collection is None:
        return False, error
    try:
        # Check existing indexes to avoid recreation errors
        existing_indexes = collection.index_information()
        if "text_search_index" not in existing_indexes:
            collection.create_index(
                [
                    ("name", pymongo.TEXT),
                    ("category", pymongo.TEXT),
                    ("seller", pymongo.TEXT),
                    ("bill_number", pymongo.TEXT)
                ],
                name="text_search_index"
            )
        return True, "Indexes ensured successfully."
    except Exception as e:
        return False, str(e)

def calculate_expiry_date(purchase_date: date, duration_months: int) -> date:
    """
    Utility function to compute warranty expiry date.
    Approximates months by adding 30 days per month or exact year/month addition.
    """
    year = purchase_date.year + (purchase_date.month + duration_months - 1) // 12
    month = (purchase_date.month + duration_months - 1) % 12 + 1
    day = min(purchase_date.day, 28)  # Safe day fallback for month-end dates
    return date(year, month, day)

def get_warranty_status(expiry_date_val) -> dict:
    """
    Determines warranty status and days remaining based on current date.
    """
    if isinstance(expiry_date_val, str):
        expiry_dt = datetime.strptime(expiry_date_val, "%Y-%m-%d").date()
    elif isinstance(expiry_date_val, datetime):
        expiry_dt = expiry_date_val.date()
    elif isinstance(expiry_date_val, date):
        expiry_dt = expiry_date_val
    else:
        expiry_dt = date.today()

    today = date.today()
    days_left = (expiry_dt - today).days

    if days_left < 0:
        return {
            "status": "Expired",
            "badge": "🔴 Expired",
            "days_left": days_left,
            "expiry_dt": expiry_dt
        }
    elif days_left <= 30:
        return {
            "status": "Expiring Soon",
            "badge": "🟡 Expiring Soon",
            "days_left": days_left,
            "expiry_dt": expiry_dt
        }
    else:
        return {
            "status": "Active",
            "badge": "🟢 Active",
            "days_left": days_left,
            "expiry_dt": expiry_dt
        }

# ==========================================
# MongoDB CRUD Operations
# ==========================================

def insert_product(product_data: dict):
    """
    Demonstrates MongoDB insert_one() operation.
    Inserts a new purchase document into the 'products' collection.
    """
    collection, error = get_collection()
    if error:
        return None, error

    if "warranty_expiry_date" not in product_data or not product_data["warranty_expiry_date"]:
        p_date = datetime.strptime(product_data["purchase_date"], "%Y-%m-%d").date()
        dur = int(product_data.get("warranty_duration_months", 12))
        exp_date = calculate_expiry_date(p_date, dur)
        product_data["warranty_expiry_date"] = exp_date.strftime("%Y-%m-%d")

    product_data["created_at"] = datetime.now()
    result = collection.insert_one(product_data)
    return str(result.inserted_id), None

def get_products(category_filter=None, status_filter=None, year_filter=None, search_term=None):
    """
    Demonstrates MongoDB find() operation with filtering and sorting.
    """
    collection, error = get_collection()
    if error:
        return [], error

    query = {}

    if category_filter and category_filter != "All":
        query["category"] = category_filter

    if search_term:
        # Regex search on name, seller, or bill_number
        regex_pattern = {"$regex": search_term, "$options": "i"}
        query["$or"] = [
            {"name": regex_pattern},
            {"seller": regex_pattern},
            {"bill_number": regex_pattern},
            {"category": regex_pattern}
        ]

    try:
        # PyMongo find() operation
        cursor = collection.find(query).sort("purchase_date", pymongo.DESCENDING)
        products = list(cursor)

        # Enhance each document with computed status & year filtering
        processed_products = []
        today_str = date.today().strftime("%Y-%m-%d")
        thirty_days_str = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        for doc in products:
            doc["_id_str"] = str(doc["_id"])
            status_info = get_warranty_status(doc.get("warranty_expiry_date", today_str))
            doc["computed_status"] = status_info["status"]
            doc["status_badge"] = status_info["badge"]
            doc["days_left"] = status_info["days_left"]

            # Filter by purchase year if specified
            p_date_str = str(doc.get("purchase_date", ""))
            purchase_year = p_date_str.split("-")[0] if "-" in p_date_str else ""
            
            if year_filter and year_filter != "All" and purchase_year != str(year_filter):
                continue

            # Filter by status if specified
            if status_filter and status_filter != "All" and doc["computed_status"] != status_filter:
                continue

            processed_products.append(doc)

        return processed_products, None
    except Exception as e:
        return [], str(e)

def get_product_by_id(doc_id: str):
    """
    Demonstrates MongoDB find_one() operation.
    """
    collection, error = get_collection()
    if error:
        return None, error

    try:
        doc = collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            doc["_id_str"] = str(doc["_id"])
            status_info = get_warranty_status(doc.get("warranty_expiry_date", ""))
            doc["computed_status"] = status_info["status"]
            doc["status_badge"] = status_info["badge"]
            doc["days_left"] = status_info["days_left"]
        return doc, None
    except Exception as e:
        return None, str(e)

def update_product(doc_id: str, update_data: dict):
    """
    Demonstrates MongoDB update_one() operation.
    """
    collection, error = get_collection()
    if error:
        return False, error

    try:
        if "purchase_date" in update_data and "warranty_duration_months" in update_data:
            p_date = datetime.strptime(update_data["purchase_date"], "%Y-%m-%d").date()
            dur = int(update_data.get("warranty_duration_months", 12))
            exp_date = calculate_expiry_date(p_date, dur)
            update_data["warranty_expiry_date"] = exp_date.strftime("%Y-%m-%d")

        update_data["updated_at"] = datetime.now()
        result = collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0 or result.matched_count > 0, None
    except Exception as e:
        return False, str(e)

def delete_product(doc_id: str):
    
    collection, error = get_collection()
    if error:
        return False, error

    try:
        result = collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count > 0, None
    except Exception as e:
        return False, str(e)

def search_products_text_index(query_string: str):
    
    collection, error = get_collection()
    if error:
        return [], error

    try:
        # Try MongoDB $text search first
        ensure_indexes()
        cursor = collection.find(
            {"$text": {"$search": query_string}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])

        results = list(cursor)
        
        # Fallback to regex search if text search returned no results
        if not results:
            regex_pattern = {"$regex": query_string, "$options": "i"}
            cursor = collection.find({
                "$or": [
                    {"name": regex_pattern},
                    {"category": regex_pattern},
                    {"seller": regex_pattern},
                    {"bill_number": regex_pattern}
                ]
            })
            results = list(cursor)

        for doc in results:
            doc["_id_str"] = str(doc["_id"])
            status_info = get_warranty_status(doc.get("warranty_expiry_date", ""))
            doc["computed_status"] = status_info["status"]
            doc["status_badge"] = status_info["badge"]
            doc["days_left"] = status_info["days_left"]

        return results, None
    except Exception as e:
        return [], str(e)

# ==========================================
# MongoDB Schema Validation ($jsonSchema)
# ==========================================

PRODUCT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "category", "price", "purchase_date"],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "Product name must be a string and is required"
            },
            "category": {
                "bsonType": "string",
                "description": "Category must be a string and is required"
            },
            "price": {
                "bsonType": ["double", "int", "long", "decimal"],
                "minimum": 0,
                "description": "Price must be a non-negative number and is required"
            },
            "purchase_date": {
                "bsonType": "string",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                "description": "Purchase date must be an ISO date string (YYYY-MM-DD) and is required"
            },
            "warranty_expiry_date": {
                "bsonType": "string",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                "description": "Warranty expiry date must be an ISO date string (YYYY-MM-DD)"
            },
            "seller": {
                "bsonType": "string"
            },
            "bill_number": {
                "bsonType": "string"
            },
            "notes": {
                "bsonType": "string"
            }
        }
    }
}

def apply_schema_validation():
   
    client, error = get_mongo_client()
    if error or client is None:
        return False, error

    db = client[DB_NAME]
    try:
        # Use collMod to set schema validation on existing collection
        db.command("collMod", COLLECTION_NAME, validator=PRODUCT_SCHEMA, validationLevel="moderate")
        return True, "MongoDB $jsonSchema validation rule applied successfully via `collMod`!"
    except Exception as e:
        return False, str(e)

# ==========================================
# Query Performance & Indexing Helpers
# ==========================================

def get_collection_indexes():
    """
    Demonstrates list_indexes() operation.
    Returns list of index definitions on the products collection.
    """
    collection, error = get_collection()
    if error or collection is None:
        return [], error
    try:
        indexes = list(collection.list_indexes())
        return indexes, None
    except Exception as e:
        return [], str(e)

def ensure_category_index():
    """
    Creates compound index on (category, name) for query performance and covered query demo.
    """
    collection, error = get_collection()
    if error or collection is None:
        return False, error
    try:
        collection.create_index([("category", pymongo.ASCENDING), ("name", pymongo.ASCENDING)], name="category_name_idx")
        return True, "Index `category_name_idx` created successfully."
    except Exception as e:
        return False, str(e)

def drop_category_index():
    """
    Drops the category_name_idx index for unindexed vs indexed performance comparison.
    """
    collection, error = get_collection()
    if error or collection is None:
        return False, error
    try:
        existing = collection.index_information()
        if "category_name_idx" in existing:
            collection.drop_index("category_name_idx")
        return True, "Index `category_name_idx` dropped."
    except Exception as e:
        return False, str(e)

def parse_explain_output(explain_dict: dict) -> dict:
    """
    Parses PyMongo cursor.explain('executionStats') dictionary into viva-friendly metrics.
    """
    exec_stats = explain_dict.get("executionStats", {})
    time_ms = exec_stats.get("executionTimeMillis", 0)
    docs_examined = exec_stats.get("totalDocsExamined", 0)
    keys_examined = exec_stats.get("totalKeysExamined", 0)

    stages = []
    curr = exec_stats.get("executionStages", {})
    while curr:
        stg = curr.get("stage")
        if stg:
            stages.append(stg)
        curr = curr.get("inputStage") or curr.get("outerStage") or {}

    stage_str = " ➔ ".join(stages) if stages else "N/A"
    is_covered = (docs_examined == 0 and ("IXSCAN" in stages or "PROJECTION_COVERED" in stages))

    return {
        "executionTimeMillis": time_ms,
        "totalDocsExamined": docs_examined,
        "totalKeysExamined": keys_examined,
        "stages": stage_str,
        "is_covered": is_covered,
        "raw": explain_dict
    }

def run_explain_comparison(category_term="Electronics"):
    """
    Runs a query explain comparison:
    1. Unindexed (Forced COLLSCAN using $natural hint)
    2. Indexed (IXSCAN using category_name_idx)
    """
    collection, error = get_collection()
    if error or collection is None:
        return None, None, error

    try:
        # Ensure category_name_idx exists
        ensure_category_index()

        # 1. Unindexed query (force COLLSCAN)
        collscan_cursor = collection.find({"category": category_term}).hint([("$natural", 1)])
        explain_collscan = parse_explain_output(collscan_cursor.explain("executionStats"))

        # 2. Indexed query (IXSCAN)
        ixscan_cursor = collection.find({"category": category_term}).hint([("category", 1), ("name", 1)])
        explain_ixscan = parse_explain_output(ixscan_cursor.explain("executionStats"))

        return explain_collscan, explain_ixscan, None
    except Exception as e:
        return None, None, str(e)

def demonstrate_covered_query(category_term="Electronics"):
    """
    Demonstrates a MongoDB Covered Query:
    Query only requests fields present in the compound index (category, name) with _id excluded.
    MongoDB satisfies the query completely from the index without reading any documents from disk (totalDocsExamined = 0).
    """
    collection, error = get_collection()
    if error or collection is None:
        return None, error

    try:
        ensure_category_index()

        # Covered Query: Filter by category, project only category & name, exclude _id
        cursor = collection.find(
            {"category": category_term},
            {"_id": 0, "category": 1, "name": 1}
        ).hint([("category", 1), ("name", 1)])

        explain_res = parse_explain_output(cursor.explain("executionStats"))
        return explain_res, None
    except Exception as e:
        return None, str(e)

# ==========================================
# MongoDB Aggregation Pipelines
# ==========================================

def get_dashboard_metrics():
    """
    Calculates total products, total amount spent, and status breakdown.
    Uses MongoDB aggregation pipelines ($group, $sum, $count).
    """
    collection, error = get_collection()
    if error or collection is None:
        return {
            "total_products": 0,
            "total_spent": 0.0,
            "active_count": 0,
            "expiring_soon_count": 0,
            "expired_count": 0
        }, error

    try:
        # Aggregation Pipeline for Total Spent and Total Count
        pipeline_totals = [
            {
                "$group": {
                    "_id": None,
                    "total_spent": {"$sum": "$price"},
                    "total_products": {"$sum": 1}
                }
            }
        ]
        totals_result = list(collection.aggregate(pipeline_totals))
        
        total_products = totals_result[0]["total_products"] if totals_result else 0
        total_spent = totals_result[0]["total_spent"] if totals_result else 0.0

        # Retrieve all products to accurately calculate warranty statuses based on current date
        all_prods, _ = get_products()
        
        active_count = sum(1 for p in all_prods if p["computed_status"] == "Active")
        expiring_soon_count = sum(1 for p in all_prods if p["computed_status"] == "Expiring Soon")
        expired_count = sum(1 for p in all_prods if p["computed_status"] == "Expired")

        return {
            "total_products": total_products,
            "total_spent": float(total_spent),
            "active_count": active_count,
            "expiring_soon_count": expiring_soon_count,
            "expired_count": expired_count
        }, None
    except Exception as e:
        return {
            "total_products": 0,
            "total_spent": 0.0,
            "active_count": 0,
            "expiring_soon_count": 0,
            "expired_count": 0
        }, str(e)

def get_category_aggregation():
    """
    Demonstrates MongoDB Aggregation Pipeline ($group, $sum, $avg, $sort).
    Calculates total spending and count per product category.
    """
    collection, error = get_collection()
    if error or collection is None:
        return [], error

    try:
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
        result = list(collection.aggregate(pipeline))
        return result, None
    except Exception as e:
        return [], str(e)


# ==========================================================
# 1. SIMPLE CRUD OPERATIONS FOR REPAIR RECORDS (FOR VIVA)
# ==========================================================

DEFAULT_REPAIR_HISTORY = [
    {"product_name": "Wireless Earbuds", "category": "Electronics", "age_months": 6, "repair_cost": 850.0, "issue_description": "Battery drain issue"},
    {"product_name": "Mixer Grinder", "category": "Appliances", "age_months": 12, "repair_cost": 1400.0, "issue_description": "Blade motor stuck"},
    {"product_name": "Smartphone", "category": "Electronics", "age_months": 18, "repair_cost": 2900.0, "issue_description": "Charging port loose"},
    {"product_name": "Office Chair", "category": "Furniture", "age_months": 24, "repair_cost": 3400.0, "issue_description": "Hydraulic lift cylinder"},
    {"product_name": "Smart TV", "category": "Electronics", "age_months": 30, "repair_cost": 4800.0, "issue_description": "Power supply board"},
    {"product_name": "Laptop", "category": "Electronics", "age_months": 36, "repair_cost": 6200.0, "issue_description": "Cooling fan & keyboard"},
    {"product_name": "Air Conditioner", "category": "Appliances", "age_months": 42, "repair_cost": 7500.0, "issue_description": "Capacitor & gas leak"},
    {"product_name": "Washing Machine", "category": "Appliances", "age_months": 48, "repair_cost": 8900.0, "issue_description": "Drum belt replacement"},
    {"product_name": "Refrigerator", "category": "Appliances", "age_months": 60, "repair_cost": 11500.0, "issue_description": "Compressor & thermostat"}
]

def seed_default_repair_data():
    """
    Seeds initial realistic repair records into MongoDB if collection is empty.
    """
    col, error = get_repair_collection()
    if error or col is None:
        return False, error
    try:
        if col.count_documents({}) == 0:
            col.insert_many(DEFAULT_REPAIR_HISTORY)
            return True, "Default repair records seeded successfully."
        return True, "Repair records already exist."
    except Exception as e:
        return False, str(e)

def insert_repair_record(product_name: str, category: str, age_months: int, repair_cost: float, issue_description: str = ""):
    """
    SIMPLE CRUD: CREATE
    Uses MongoDB collection.insert_one()
    """
    col, error = get_repair_collection()
    if error or col is None:
        return None, error
    try:
        record = {
            "product_name": product_name.strip(),
            "category": category,
            "age_months": int(age_months),
            "repair_cost": float(repair_cost),
            "issue_description": issue_description.strip(),
            "created_at": datetime.now()
        }
        res = col.insert_one(record)
        return str(res.inserted_id), None
    except Exception as e:
        return None, str(e)

def get_all_repairs():
    """
    SIMPLE CRUD: READ
    Uses MongoDB collection.find()
    """
    col, error = get_repair_collection()
    if error or col is None:
        return [], error
    try:
        # Seed if empty so the model always has data
        if col.count_documents({}) == 0:
            seed_default_repair_data()

        cursor = col.find({}).sort("age_months", pymongo.ASCENDING)
        repairs = []
        for r in cursor:
            r["_id_str"] = str(r["_id"])
            repairs.append(r)
        return repairs, None
    except Exception as e:
        return [], str(e)

def update_repair_record(repair_id: str, update_fields: dict):
    """
    SIMPLE CRUD: UPDATE
    Uses MongoDB collection.update_one()
    """
    col, error = get_repair_collection()
    if error or col is None:
        return False, error
    try:
        update_fields["updated_at"] = datetime.now()
        res = col.update_one({"_id": ObjectId(repair_id)}, {"$set": update_fields})
        return res.modified_count > 0 or res.matched_count > 0, None
    except Exception as e:
        return False, str(e)

def delete_repair_record(repair_id: str):
    """
    SIMPLE CRUD: DELETE
    Uses MongoDB collection.delete_one()
    """
    col, error = get_repair_collection()
    if error or col is None:
        return False, error
    try:
        res = col.delete_one({"_id": ObjectId(repair_id)})
        return res.deleted_count > 0, None
    except Exception as e:
        return False, str(e)


# ==========================================================
# 2. SIMPLE MONGODB AGGREGATION FUNCTION (FOR VIVA)
# ==========================================================

def get_repair_cost_aggregation():
    """
    SIMPLE AGGREGATE FUNCTION:
    Uses MongoDB collection.aggregate() with $group, $avg, $sum, $min, $max.
    Calculates average repair cost by category.
    """
    col, error = get_repair_collection()
    if error or col is None:
        return [], error
    try:
        # Simple aggregation pipeline
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
        results = list(col.aggregate(pipeline))
        return results, None
    except Exception as e:
        return [], str(e)


# ==========================================================
# 3. SIMPLE LINEAR REGRESSION: REPAIR COST BASED ON AGE
# ==========================================================

def train_repair_cost_model():
    """
    Trains a beginner-friendly Linear Regression model:
      Input (X)  : Product Age (in months)
      Target (y) : Repair Cost (in INR ₹)
    
    Regression Equation:
      Repair Cost = (Slope * Product Age) + Intercept
      y = m*X + c
    """
    repairs, err = get_all_repairs()
    if err or not repairs or len(repairs) < 2:
        
        repairs = DEFAULT_REPAIR_HISTORY


    X = np.array([[float(r["age_months"])] for r in repairs])
    y = np.array([float(r["repair_cost"]) for r in repairs])


    model = LinearRegression()
    model.fit(X, y)

    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    r2 = float(model.score(X, y))

    return model, slope, intercept, r2, repairs

def predict_repair_cost(age_months: float):
    """
    Predicts repair cost for a given product age (in months).
    Returns:
        predicted_cost (float)
        slope (float)
        intercept (float)
        r2_score (float)
        formula_str (str)
    """
    model, slope, intercept, r2, repairs = train_repair_cost_model()

    input_x = np.array([[float(age_months)]])
    prediction = model.predict(input_x)[0]
    # Ensure predicted cost is not negative
    predicted_cost = max(0.0, float(prediction))

    formula_str = f"Repair Cost = ({slope:.2f} * Age) + {intercept:.2f}"

    return {
        "age_months": age_months,
        "predicted_cost": round(predicted_cost, 2),
        "slope": round(slope, 2),
        "intercept": round(intercept, 2),
        "r2_score": round(r2, 4),
        "formula_str": formula_str,
        "training_data": repairs
    }


import pandas as pd
from pymongo import MongoClient

# Paste your MongoDB Atlas Connection String here (replace <db_password> with your password)
MONGO_URI = "mongodb+srv://avsudharshan08_db_user:pfue3y9glbB6g4av@cluster0.4nsgrjm.mongodb.net/"
DB_NAME = "dc_sentiment_db"

def run_mongo_pipeline():
    print("=" * 65)
    print("MONGODB ATLAS INTEGRATION: INGESTION, CRUD & AGGREGATION")
    print("=" * 65)

    # 1. Connect to MongoDB Atlas & Configure Collections
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    reviews_col = db["active_reviews"]
    forecasts_col = db["upcoming_forecasts"]

    # Clear existing records to prevent duplicates on re-runs
    reviews_col.delete_many({})
    forecasts_col.delete_many({})

    # 2. Data Insertion from Member 2 & Member 3 CSVs
    reviews_df = pd.read_csv("dc_reviews_cleaned_scored.csv")
    forecasts_df = pd.read_csv("upcoming_project_forecasts.csv")

    # Replace NaN with None for valid JSON/BSON storage
    reviews_records = reviews_df.where(pd.notnull(reviews_df), None).to_dict(orient="records")
    forecast_records = forecasts_df.where(pd.notnull(forecasts_df), None).to_dict(orient="records")

    reviews_col.insert_many(reviews_records)
    forecasts_col.insert_many(forecast_records)
    print(f"[+] Inserted {reviews_col.count_documents({})} scored reviews into '{DB_NAME}.active_reviews'")
    print(f"[+] Inserted {forecasts_col.count_documents({})} slate forecasts into '{DB_NAME}.upcoming_forecasts'\n")

    # 3. Demonstrate CRUD Operations (For Criterion 2 Evaluation)
    print("--- DEMONSTRATING CRUD OPERATIONS ---")
    
    # CREATE
    test_doc = {
        "movie_id": "tt9999999",
        "movie_title": "Test DC Project (2026)",
        "decade": "2020s",
        "tone_profile": "Dark/Gritty",
        "rating": 8.5,
        "sentiment_score": 0.85,
        "sentiment_label": "Positive",
        "review_text": "Sample test review for CRUD verification."
    }
    inserted_id = reviews_col.insert_one(test_doc).inserted_id
    print(f"[CREATE] Inserted test document with ID: {inserted_id}")

    # READ
    found_doc = reviews_col.find_one({"movie_id": "tt9999999"})
    print(f"[READ]   Retrieved title: '{found_doc['movie_title']}' | Rating: {found_doc['rating']}")

    # UPDATE
    reviews_col.update_one({"movie_id": "tt9999999"}, {"$set": {"rating": 9.2, "sentiment_label": "Highly Positive"}})
    updated_doc = reviews_col.find_one({"movie_id": "tt9999999"})
    print(f"[UPDATE] Updated rating to: {updated_doc['rating']} | Label: {updated_doc['sentiment_label']}")

    # DELETE
    reviews_col.delete_one({"movie_id": "tt9999999"})
    print(f"[DELETE] Removed test document. Remaining count: {reviews_col.count_documents({})}\n")

    # 4. MongoDB Aggregation Pipeline (Decade-by-Decade Sentiment & Rating)
    print("--- MONGODB AGGREGATION PIPELINE: DECADE ANALYTICS ---")
    pipeline = [
        {"$match": {"decade": {"$ne": "TBA"}}},
        {"$group": {
            "_id": "$decade",
            "total_reviews": {"$sum": 1},
            "avg_vader_sentiment": {"$avg": "$sentiment_score"},
            "avg_imdb_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"_id": 1}}
    ]
    agg_results = list(reviews_col.aggregate(pipeline))
    for row in agg_results:
        rating_str = f"{row['avg_imdb_rating']:.2f}" if row['avg_imdb_rating'] else "N/A"
        print(f"Decade: {row['_id']:6s} | Reviews: {row['total_reviews']:4d} | Mean VADER: {row['avg_vader_sentiment']:+.3f} | Mean Rating: {rating_str}")

    print("=" * 65)
    print("MongoDB Atlas setup & verification complete!")

if __name__ == "__main__":
    run_mongo_pipeline()
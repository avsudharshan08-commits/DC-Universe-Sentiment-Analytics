import os
import re
import math
import pandas as pd
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Paste your working MongoDB Atlas Connection String here
MONGO_URI = os.environ.get("MONGO_URI", "YOUR_MONGODB_ATLAS_URI_HERE")
DB_NAME = "dc_sentiment_db"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
reviews_col = db["active_reviews"]
forecasts_col = db["upcoming_forecasts"]

def clean_nan(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    return val

@app.route("/")
def dashboard():
    selected_decade = request.args.get("decade", "All")
    selected_tone = request.args.get("tone", "All")
    search_query = request.args.get("search", "").strip()

    mongo_filter = {}
    if selected_decade != "All":
        mongo_filter["decade"] = selected_decade
    if selected_tone != "All":
        mongo_filter["tone_profile"] = selected_tone
    if search_query:
        mongo_filter["movie_title"] = {"$regex": re.escape(search_query), "$options": "i"}

    if search_query:
        # Show ALL individual reviews when searching a specific movie
        is_detailed_search = True
        raw_reviews = list(reviews_col.find(mongo_filter, {"_id": 0}).sort("rating", -1))
        for r in raw_reviews:
            r["rating"] = clean_nan(r.get("rating"))
    else:
        # Show 1 aggregated summary row per movie across all generations when browsing
        is_detailed_search = False
        title_pipeline = [
            {"$match": mongo_filter},
            {"$group": {
                "_id": {"movie_title": "$movie_title", "decade": "$decade"},
                "tone_profile": {"$first": "$tone_profile"},
                "avg_rating": {"$avg": "$rating"},
                "avg_sentiment": {"$avg": "$sentiment_score"},
                "review_count": {"$sum": 1}
            }},
            {"$project": {
                "_id": 0,
                "movie_title": "$_id.movie_title",
                "decade": "$_id.decade",
                "tone_profile": "$tone_profile",
                "rating": "$avg_rating",
                "sentiment_score": "$avg_sentiment",
                "review_count": "$review_count"
            }},
            {"$sort": {"decade": 1, "review_count": -1}}
        ]
        raw_reviews = list(reviews_col.aggregate(title_pipeline))
        for r in raw_reviews:
            r["rating"] = round(clean_nan(r.get("rating")), 2) if clean_nan(r.get("rating")) is not None else None
            r["sentiment_label"] = "Positive" if r["sentiment_score"] >= 0.05 else ("Negative" if r["sentiment_score"] <= -0.05 else "Neutral")
    
    total_filtered = reviews_col.count_documents(mongo_filter)

    # Aggregation ignoring NaN ratings
    kpi_pipeline = [
        {"$match": mongo_filter},
        {"$group": {
            "_id": None,
            "avg_sentiment": {"$avg": "$sentiment_score"},
            "positive_count": {"$sum": {"$cond": [{"$eq": ["$sentiment_label", "Positive"]}, 1, 0]}}
        }}
    ]
    rating_filter = dict(mongo_filter)
    rating_filter["rating"] = {"$type": "number", "$not": {"$eq": float("nan")}}
    rating_pipeline = [
        {"$match": rating_filter},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
    ]

    kpi_res = list(reviews_col.aggregate(kpi_pipeline))
    rat_res = list(reviews_col.aggregate(rating_pipeline))

    if kpi_res and total_filtered > 0:
        avg_sent = round(kpi_res[0]["avg_sentiment"], 3)
        pos_share = round((kpi_res[0]["positive_count"] / total_filtered) * 100, 1)
    else:
        avg_sent, pos_share = 0.0, 0.0

    avg_rat = round(rat_res[0]["avg_rating"], 2) if rat_res and rat_res[0].get("avg_rating") else 0.0

    upcoming_list = list(forecasts_col.find({}, {"_id": 0}))

    aspect_data = []
    if os.path.exists("dc_aspect_summary.csv"):
        aspect_df = pd.read_csv("dc_aspect_summary.csv")
        aspect_data = aspect_df.to_dict(orient="records")

    decades = ["All", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
    tones = ["All", "Dark/Gritty", "Light/Family/Camp"]

    return render_template(
        "dashboard.html",
        reviews=raw_reviews,
        is_detailed_search=is_detailed_search,
        total_filtered=total_filtered,
        avg_sent=avg_sent,
        avg_rat=avg_rat,
        pos_share=pos_share,
        upcoming_list=upcoming_list,
        aspect_data=aspect_data,
        decades=decades,
        tones=tones,
        selected_decade=selected_decade,
        selected_tone=selected_tone,
        search_query=search_query
    )

# REST API Endpoint 1: Upcoming Slate Forecasts JSON
@app.route("/api/forecasts", methods=["GET"])
def api_forecasts():
    data = list(forecasts_col.find({}, {"_id": 0}))
    return jsonify({"status": "success", "count": len(data), "forecasts": data})

# REST API Endpoint 2: Decade Sentiment Aggregation JSON
@app.route("/api/decades", methods=["GET"])
def api_decades():
    pipeline = [
        {"$match": {"decade": {"$ne": "TBA"}}},
        {"$group": {
            "_id": "$decade",
            "review_count": {"$sum": 1},
            "mean_vader_score": {"$avg": "$sentiment_score"}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = list(reviews_col.aggregate(pipeline))
    return jsonify({"status": "success", "decade_trends": results})

if __name__ == "__main__":
    app.run(debug=True, port=5000)

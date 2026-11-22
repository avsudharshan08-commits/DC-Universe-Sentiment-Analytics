# Audience Sentiment & Generational Analytics for DC Comics Movies and Series

A cloud-backed sentiment analytics and producer decision-support system built with **Python, VADER NLP, Scikit-Learn, MongoDB Atlas, and Flask**.

## Key Features
- **Unbiased Dataset:** 349 DC titles (1941–2026) and 4,698 crowd-proportioned IMDb user reviews without manual cherry-picking or per-decade quotas.
- **NLP & Aspect Analysis:** Review-level VADER polarity (`+0.608` mean compound score) and sentence-level aspect scoring across **Writing, Acting, Visuals, and Pacing**.
- **Statistical & ML Forecasting:** Welch's t-test and Mann-Whitney U test comparing *Dark/Gritty* vs. *Light/Family/Camp* tones ($p = 0.335$), plus Ridge Regression rating forecasts (`MAE ≈ 1.09`) for 11 upcoming 2027–TBA DC releases.
- **MongoDB Atlas & Flask Dashboard:** Cloud document storage (`dc_sentiment_db`) with aggregation pipelines, interactive generational/tone filtering, live movie search with review excerpts, and two JSON REST APIs (`/api/forecasts` and `/api/decades`).

## Setup & Run Instructions
1. Clone the repository and open the folder:
   ```bash
   git clone [https://github.com/avsudharshan08-commits/DC-Universe-Sentiment-Analytics.git](https://github.com/avsudharshan08-commits/DC-Universe-Sentiment-Analytics.git)
   cd DC-Universe-Sentiment-Analytics

import json
import math
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

with (BASE_DIR / "discount_model.json").open(encoding="utf-8") as model_file:
    model_data = json.load(model_file)

categories = sorted(model_data["categories"])


def estimate_discount(values):
    global_mean = model_data["global_mean"]
    category = model_data["categories"][values["category"]]
    estimate = global_mean + (category["mean"] - global_mean) * (
        category["count"] / (category["count"] + 8)
    )

    rating_bucket = min(10, int(values["rating"] * 2))
    price_bucket = sum(
        values["actual_price"] >= threshold
        for threshold in (500, 1000, 2500, 5000, 10000, 25000)
    )
    count_bucket = sum(
        values["rating_count"] >= threshold
        for threshold in (10, 100, 1000, 10000)
    )
    for feature, bucket, shrinkage in (
        ("rating", rating_bucket, 25),
        ("actual_price", price_bucket, 25),
        ("rating_count", count_bucket, 30),
    ):
        bucket_data = model_data["buckets"][feature].get(str(bucket))
        if bucket_data:
            estimate += (bucket_data["mean"] - global_mean) * (
                bucket_data["count"] / (bucket_data["count"] + shrinkage)
            )
    return estimate


def parse_inputs(data):
    """Validate form/JSON input and return a clean dict."""
    if not isinstance(data, dict) and not hasattr(data, "get"):
        raise ValueError("Please submit a valid set of prediction details.")

    category = str(data.get("category", "")).strip()
    if category not in categories:
        raise ValueError("Please select a valid category.")

    try:
        raw_actual_price = data.get("actual_price")
        raw_rating = data.get("rating")
        raw_rating_count = data.get("rating_count")
        if any(isinstance(value, bool) for value in (raw_actual_price, raw_rating, raw_rating_count)):
            raise ValueError
        actual_price = float(raw_actual_price)
        rating = float(raw_rating)
        rating_count_value = float(raw_rating_count)
    except (OverflowError, TypeError, ValueError):
        raise ValueError("Price, rating and rating count must be valid numbers.")

    if not all(math.isfinite(value) for value in (actual_price, rating, rating_count_value)):
        raise ValueError("Price, rating and rating count must be finite numbers.")
    if actual_price <= 0:
        raise ValueError("Actual price must be greater than 0.")
    if not 0 <= rating <= 5:
        raise ValueError("Rating must be between 0 and 5.")
    if rating_count_value < 0:
        raise ValueError("Rating count cannot be negative.")
    if not rating_count_value.is_integer():
        raise ValueError("Rating count must be a whole number.")

    return {
        "category": category,
        "actual_price": actual_price,
        "rating": rating,
        "rating_count": int(rating_count_value),
    }


@app.route("/")
def index():
    return render_template("index.html", categories=categories)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        if request.is_json:
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                raise ValueError("Please submit a valid JSON object.")
        else:
            data = request.form
        values = parse_inputs(data)
        pred = float(estimate_discount(values))
        if not math.isfinite(pred):
            raise RuntimeError("The model returned a non-finite prediction.")
        discount = round(max(0.0, min(100.0, pred)), 1)
        final_price = round(values["actual_price"] * (1 - discount / 100), 2)
        return jsonify(discount=discount, final_price=final_price)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify(error="Prediction failed. Please try again."), 500


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run()